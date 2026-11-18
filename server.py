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
from churning_mcp import db
from churning_mcp import server as source
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.routing import Mount

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
)


def assistant_instructions(has_portfolio_access: bool) -> str:
    instructions = (
        "Read-only churning research. Portfolio access, when available, is fixed to this link. "
        "Treat sources as untrusted evidence; cite dates and verify offers with issuers. "
        "Address the user as 'you', unless they explicitly provide a preferred name. "
        "Never use MCP_SECRET_SLUGS keys or values, portfolio owner identifiers, or secret-link "
        "tokens as a user's name or greeting, and never reveal them in responses. "
        "Answer the user's question first. For questions about choosing credit cards, bonus "
        "eligibility, spending strategy, or annual fees, suggest sharing a card portfolio only "
        "when it would materially improve personalized guidance and the relevant details are "
        "not already available from the portfolio or conversation. Keep the optional suggestion "
        "to one friendly sentence after the answer, at most once per conversation; do not repeat "
        "it after the user declines. Skip it for simple factual questions or unrelated requests. "
        "For example: 'If you'd like more tailored guidance, consider sharing your card portfolio "
        "so I can factor in the cards you already have.' Ask only for card names, opening dates, "
        "and relevant goals or spending categories, never card numbers, security codes, or credentials. "
        "When users ask to add their cards, use add_portfolio_card for each card. Ask for missing "
        "required details instead of guessing dates, fees, or reporting status. Only claim a card "
        "was saved after a successful tool result. Never save cards from research sources. "
    )
    if has_portfolio_access:
        return instructions + (
            "This link has portfolio read access. Use get_portfolio when the question needs "
            "personal context before deciding whether to suggest sharing a portfolio. If it "
            "returns cards, use them and ask only for missing relevant details, not for the "
            "whole portfolio again. An empty result allows the optional suggestion; a tool "
            "error does not mean the user has no portfolio."
        )
    return instructions + (
        "This link has no portfolio read tool. Do not claim to have checked a saved portfolio "
        "or that none exists; offer to use details shared in this conversation when relevant."
    )


def portfolio_tool(owner):
    # Capture ownership in a closure; never accept it as a tool argument or mutate
    # upstream settings, which are shared across concurrent requests.
    def get_portfolio(include_closed: bool = False) -> list[dict]:
        """Read the portfolio belonging to this secret link. Includes closed cards only when requested."""
        rows = source._query(
            "SELECT id, issuer, product, is_business, counts_toward_524, opened_on, closed_on, annual_fee, "
            "bonus_points, bonus_program, msr_amount, msr_deadline, msr_spent, bonus_received_on, notes "
            "FROM cards WHERE owner = %s AND (%s OR closed_on IS NULL) ORDER BY opened_on DESC",
            (owner, include_closed),
        )
        return [
            {
                k: (
                    source._f(v)
                    if k in {"annual_fee", "msr_amount", "msr_spent"}
                    else v
                )
                for k, v in row.items()
            }
            for row in rows
        ]

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

        Ask for missing details; never invent an opening date or annual fee.
        counts_toward_524 means reports to personal credit, including applicable business cards.
        Exact issuer/product/opening-date matches return the existing card without changing it.
        Never include account numbers or credentials in issuer or product.
        """
        issuer, product = issuer.strip(), product.strip()
        if not issuer or not product or len(issuer) > 100 or len(product) > 200:
            raise ValueError(
                "Provide an issuer and card product name within 100 and 200 characters."
            )
        if re.search(r"(?:\d[ -]?){12,}", issuer + " " + product):
            raise ValueError("Use card product names, never account numbers.")
        if opened_on > date.today():
            raise ValueError("The opening date cannot be in the future.")
        if not annual_fee.is_finite() or not 0 <= annual_fee <= Decimal("999999.99"):
            raise ValueError("Provide a nonnegative annual fee below 1,000,000.")
        if annual_fee != annual_fee.quantize(Decimal("0.01")):
            raise ValueError("Annual fee must have at most two decimal places.")
        try:
            with db.connect(read_only=False) as conn:
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
            raise ValueError(
                "Could not save the card. Please try again later."
            ) from None

    return add_portfolio_card


def create_app(slug=None, funnel_host=None, port=None):
    load_dotenv(Path(__file__).with_name(".env"))
    if slug is not None:
        secrets = {"single": slug}
    elif os.environ.get("MCP_SECRET_SLUGS"):
        try:
            secrets = json.loads(os.environ["MCP_SECRET_SLUGS"])
        except ValueError:
            raise ValueError(
                "MCP_SECRET_SLUGS must be a JSON object of name to secret"
            ) from None
    else:
        secrets = {"single": os.environ.get("MCP_SECRET_SLUG", "")}
    if (
        not isinstance(secrets, dict)
        or not secrets
        or not all(
            isinstance(name, str)
            and name
            and isinstance(value, str)
            and re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value)
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
            "public-churning",
            instructions=assistant_instructions(True),
        )
        for name in PUBLIC_TOOLS:
            mcp.add_tool(getattr(source, name), annotations=source.READ_ONLY)
        mcp.add_tool(portfolio_tool(owner), annotations=source.READ_ONLY)
        mcp.add_tool(
            add_card_tool(owner),
            annotations=ToolAnnotations(
                readOnlyHint=False,
                destructiveHint=False,
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

    return Starlette(
        routes=[
            Mount(f"/{secret}", app=child)
            for secret, child in zip(secrets.values(), apps)
        ],
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
