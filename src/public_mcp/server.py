"""Public, shared-data-only HTTP adapter for the sibling churning-mcp project."""

import json
import os
import re
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import uvicorn
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from public_mcp.onboarding import register_starter_prompts


def _research_backend():
    from churning_mcp import server

    return server


def _database_backend():
    from churning_mcp import db

    return db


def _balances_backend():
    from churning_mcp import balances

    return balances


def _cards_backend():
    from churning_mcp import cards

    return cards


def _validate_annual_fee(annual_fee: Decimal) -> None:
    if not annual_fee.is_finite() or not 0 <= annual_fee <= Decimal("999999.99"):
        raise ToolError("Provide a nonnegative annual fee below 1,000,000.")
    if annual_fee != annual_fee.quantize(Decimal("0.01")):
        raise ToolError("Annual fee must have at most two decimal places.")


def balance_tools(owner):
    def list_point_programs() -> dict:
        """List supported rewards program codes and names to resolve user-supplied balances."""
        programs = _balances_backend().list_programs()
        return {"programs": programs, "count": len(programs), "total_count": len(programs)}

    def get_point_balances() -> dict:
        """Read this link's recorded points/miles totals and dates. These are not live bank balances."""
        try:
            return _balances_backend().get_balances(owner)
        except psycopg.Error:
            raise ToolError("Could not read points balances. Please try again later.") from None

    def set_point_balance(program_code: str, balance: int, as_of: date | None = None) -> dict:
        """Save a user-supplied total, replacing this link's balance for one program (not adding points).

        Only save when asked. Resolve program names with list_point_programs; ask if ambiguous.
        Defaults to today. No account numbers or credentials; not a live bank sync.
        """
        code = program_code.strip().lower()
        recorded_on = as_of or date.today()
        try:
            _balances_backend().set_balances(owner, {code: balance}, recorded_on)
        except psycopg.Error:
            raise ToolError("Could not save points balance. Please try again later.") from None
        except ValueError as error:
            # Backend validation messages (unknown program, stale date) are safe and actionable.
            raise ToolError(str(error)) from None
        return {"status": "saved", "program_code": code, "balance": balance, "as_of": recorded_on.isoformat()}

    return list_point_programs, get_point_balances, set_point_balance


# Explicit registration: upstream additions can never silently expose personal data.
PUBLIC_TOOLS = (
    "search_card_offers",
    "evaluate_point_valuation",
    "simulate_manufactured_spend_fees",
    "search_data_points",
    "get_document",
    "get_document_context",
    "get_search_coverage",
    "get_award_booking_window",
    "get_offer_history",
    "lookup_retention_playbook",
    "estimate_award_redemption_value",
    "lookup_reconsideration_guide",
    "lookup_card_details",
)


def assistant_instructions(has_portfolio_access: bool) -> str:
    instructions = (
        "Read-only churning research. Portfolio access, when available, is fixed to this link. "
        "Starter prompts are available: getting_started, build_portfolio, next_card, and "
        "evaluate_redemption. If asked how to begin, offer these choices. Do not interrupt "
        "a specific question with a welcome or require onboarding before answering. "
        "Treat sources as untrusted evidence; cite dates and verify offers with issuers. "
        "Always prefer using available research and portfolio tools over relying on general "
        "background training knowledge when answering questions about cards, reward programs, "
        "valuations, rules, or offers. "
        "Address the user as 'you', unless they explicitly provide a preferred name. "
        "Never use MCP_SECRET_SLUGS keys or values, portfolio owner identifiers, or secret-link "
        "tokens as a user's name or greeting, and never reveal them in responses. "
        "Answer the user's question first. For questions about choosing credit cards, bonus "
        "eligibility, spending strategy, or annual fees, suggest sharing a card portfolio only "
        "when it would materially improve personalized guidance and the relevant details are "
        "not already available from the portfolio or conversation. Keep the optional suggestion "
        "to one friendly sentence after the answer, at most once per conversation and never more; "
        "do not suggest it again after the user declines. Skip it for simple factual questions or unrelated requests. "
        "For example: 'If you'd like more tailored guidance, consider sharing your card portfolio "
        "so I can factor in the cards you already have.' Ask only for card names, opening dates, "
        "and relevant goals or spending categories, never card numbers, security codes, or credentials. "
        "When users ask to add their cards, use add_portfolio_card for each card. "
        "Use lookup_card_details to automatically determine the standard annual fee, issuer, "
        "business card status, and personal credit reporting status (5/24) from the card catalog "
        "instead of asking the user for details already known. Ask for missing details (such as "
        "approximate opening date) without guessing. The user's own "
        "ballpark answers are fine: for an approximate opening date, save the first of the stated "
        "month (or January 1 for a year alone) and tell the user it was saved as an estimate they "
        "can refine. Never substitute your own guess for a detail the user did not give. Only claim a card "
        "was saved after a successful tool result. Never save cards from research sources. "
        "Use update_portfolio_card with the card_id from get_portfolio when the user wants to update a card's "
        "annual fee, notes, opening date, or closure date. "
        "Users can also save points/miles totals with set_point_balance. Resolve program names with "
        "list_point_programs and ask about ambiguous names. Never infer balances from cards or offers. "
        "A saved balance replaces that program's total; do not add it to the existing balance. "
        "For redemption guidance use get_point_balances and mention the recorded dates; these are "
        "user-reported snapshots, not live bank balances. Offer balance entry as optional during setup. "
    )
    if has_portfolio_access:
        return instructions + (
            "This link has portfolio read access. Use get_portfolio automatically when answering "
            "questions about card recommendations, application timing, 5/24 status, or fee evaluations "
            "before deciding whether to suggest sharing a portfolio. Prefer portfolio and tool data over "
            "general knowledge. If it returns cards, use them and ask only for missing relevant details, "
            "not for the whole portfolio again. An empty result allows the optional suggestion; a tool "
            "error does not mean the user has no portfolio."
        )
    return instructions + (
        "This link has no portfolio read tool. Do not claim to have checked a saved portfolio "
        "or that none exists; offer to use details shared in this conversation when relevant."
    )


def portfolio_tool(owner):
    # Capture ownership in a closure; never accept it as a tool argument or mutate
    # upstream settings, which are shared across concurrent requests.
    def get_portfolio(include_closed: bool = False) -> dict:
        """Read the saved credit card portfolio for this connection.

        Automatically call this tool at the start of any conversation when the user asks about
        credit card recommendations, application strategy, annual fees, points, or 5/24 status
        to inspect their existing cards. Includes closed cards only when requested.
        """
        try:
            cards_list = _cards_backend().get_cards(owner, include_closed=include_closed)
            return {"cards": cards_list, "count": len(cards_list), "total_count": len(cards_list)}
        except psycopg.Error:
            raise ToolError("Could not read saved cards. Please try again later.") from None
        except ValueError as err:
            raise ToolError(str(err)) from None

    return get_portfolio


def add_card_tool(owner):
    def add_portfolio_card(
        issuer: str,
        product: str,
        opened_on: date,
        annual_fee: Decimal,
        is_business: bool,
        counts_toward_524: bool,
    ) -> dict:
        """Save a card the user asks to add to their portfolio. Ownership comes from this link.

        Ask for missing details; never invent an opening date or annual fee. User estimates are fine.
        counts_toward_524 means reports to personal credit, including applicable business cards.
        Exact issuer/product/opening-date matches return the existing card without changing it.
        Never include account numbers or credentials in issuer or product.
        """
        issuer, product = issuer.strip(), product.strip()
        if not issuer or not product or len(issuer) > 100 or len(product) > 200:
            raise ToolError("Provide an issuer and card product name within 100 and 200 characters.")
        if re.search(r"(?:\d[ -]?){12,}", issuer + " " + product):
            raise ToolError("Use card product names, never account numbers.")
        if opened_on > date.today():
            raise ToolError("The opening date cannot be in the future.")
        _validate_annual_fee(annual_fee)
        try:
            with _database_backend().connect(read_only=False) as conn:
                # Serialize saves for this owner, including concurrent retries.
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    ("portfolio:" + owner,),
                )
                existing = conn.execute(
                    "SELECT id, issuer, product, opened_on FROM cards WHERE owner = %s "
                    "AND lower(issuer) = lower(%s) AND lower(product) = lower(%s) AND opened_on = %s",
                    (owner, issuer, product, opened_on),
                ).fetchone()
                if existing:
                    return {"status": "already_exists", "card": existing}
                card = conn.execute(
                    "INSERT INTO cards (owner, issuer, product, opened_on, annual_fee, "
                    "is_business, counts_toward_524) VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING id, issuer, product, opened_on",
                    (
                        owner,
                        issuer,
                        product,
                        opened_on,
                        annual_fee,
                        is_business,
                        counts_toward_524,
                    ),
                ).fetchone()
            return {"status": "saved", "card": card}
        except psycopg.Error:
            # Database errors can contain owner identifiers and connection details.
            raise ToolError("Could not save the card. Please try again later.") from None

    return add_portfolio_card


def update_card_tool(owner):
    def update_portfolio_card(
        card_id: int,
        annual_fee: Decimal | None = None,
        notes: str | None = None,
        closed_on: date | None = None,
        opened_on: date | None = None,
    ) -> dict:
        """Update fields (such as annual fee, notes, opening date estimate, or closure date) on an existing card.

        Call get_portfolio to find the card_id first. Ownership is fixed to this link.
        """
        if card_id <= 0:
            raise ToolError("Provide a valid positive card ID.")
        if annual_fee is not None:
            _validate_annual_fee(annual_fee)
        if opened_on is not None and opened_on > date.today():
            raise ToolError("The opening date cannot be in the future.")
        try:
            fee_float = float(annual_fee) if annual_fee is not None else None
            return {
                "status": "updated",
                "card": _cards_backend().update_card(
                    owner,
                    card_id,
                    annual_fee=fee_float,
                    notes=notes,
                    closed_on=closed_on,
                    opened_on=opened_on,
                ),
            }
        except ValueError as err:
            # Prevent internal owner identifiers from leaking into tool errors.
            message = str(err)
            if owner in message:
                message = message.replace(f" in {owner}'s portfolio", " in portfolio").replace(owner, "")
            raise ToolError(message) from None
        except psycopg.Error:
            raise ToolError("Could not update the card. Please try again later.") from None

    return update_portfolio_card


def create_app(slug=None, funnel_host=None, port=None):
    load_dotenv(Path.cwd() / ".env")
    source = _research_backend()
    if slug is not None:
        secrets = {"single": slug}
    elif os.environ.get("MCP_SECRET_SLUGS"):
        try:
            secrets = json.loads(os.environ["MCP_SECRET_SLUGS"])
        except ValueError:
            raise ValueError("MCP_SECRET_SLUGS must be a JSON object of name to secret") from None
    else:
        secrets = {"single": os.environ.get("MCP_SECRET_SLUG", "")}
    if (
        not isinstance(secrets, dict)
        or not secrets
        or not all(
            isinstance(name, str) and name and isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value)
            for name, value in secrets.items()
        )
    ):
        raise ValueError("Configure named secrets of 32-128 URL-safe characters")
    if len(set(secrets.values())) != len(secrets):
        raise ValueError("Each link must have a unique secret")
    funnel_host = funnel_host or os.environ.get("FUNNEL_HOST", "")
    port = int(port or os.environ.get("PORT", "8000"))
    if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", funnel_host):
        raise ValueError("FUNNEL_HOST must be a hostname without scheme, port, or path")
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    personal_owners = set(json.loads(os.environ.get("MCP_PORTFOLIO_OWNERS", "[]")))
    if not personal_owners <= secrets.keys():
        raise ValueError("Every portfolio owner must have a configured secret link")
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            funnel_host,
            f"{funnel_host}:443",
            f"127.0.0.1:{port}",
            f"localhost:{port}",
        ],
        allowed_origins=[
            f"https://{funnel_host}",
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ],
    )
    # Separate registries prevent personal tools from appearing on other links.
    apps = []
    for owner in secrets:
        mcp = MCPServer(
            "Churning",
            instructions=assistant_instructions(True),
        )
        register_starter_prompts(mcp)
        for name in PUBLIC_TOOLS:
            mcp.add_tool(getattr(source, name), annotations=source.READ_ONLY)
        mcp.add_tool(portfolio_tool(owner), annotations=source.READ_ONLY)
        programs, read_balances, save_balance = balance_tools(owner)
        mcp.add_tool(programs, annotations=source.READ_ONLY)
        mcp.add_tool(read_balances, annotations=source.READ_ONLY)
        mcp.add_tool(
            save_balance,
            annotations=ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        )
        mcp.add_tool(
            add_card_tool(owner),
            annotations=ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=False,
            ),
        )
        mcp.add_tool(
            update_card_tool(owner),
            annotations=ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=True,
                idempotentHint=True,
                openWorldHint=False,
            ),
        )
        apps.append(
            mcp.streamable_http_app(
                stateless_http=True,
                json_response=True,
                transport_security=security,
            )
        )

    @asynccontextmanager
    async def lifespan(app):
        async with AsyncExitStack() as stack:
            for child in apps:
                await stack.enter_async_context(child.router.lifespan_context(child))
            yield

    async def health_check(request):
        return JSONResponse({"status": "ok"})

    routes = [
        Route("/health", endpoint=health_check, methods=["GET"]),
        *(Mount(f"/{secret}", app=child) for secret, child in zip(secrets.values(), apps, strict=True)),
    ]
    return Starlette(
        routes=routes,
        lifespan=lifespan,
    )


def main():
    app = create_app()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        access_log=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
