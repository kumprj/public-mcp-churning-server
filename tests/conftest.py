"""Unit tests isolate the private backend and never read deployment configuration."""

from types import SimpleNamespace

import pytest
from mcp.types import ToolAnnotations

from public_mcp import server


def unavailable(*args, **kwargs):
    raise AssertionError("Unit tests must mock database and research calls")


@pytest.fixture(autouse=True)
def isolated_backend(monkeypatch):
    backend = SimpleNamespace(
        READ_ONLY=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
        _query=unavailable,
        _f=lambda value: None if value is None else float(value),
    )

    def research_tool(name):
        def tool() -> dict:
            """Test double for upstream tool registration; never queries research data."""
            return unavailable()

        tool.__name__ = name
        return tool

    for name in server.PUBLIC_TOOLS:
        setattr(backend, name, research_tool(name))
    database = SimpleNamespace(connect=unavailable)
    monkeypatch.setattr(server, "_research_backend", lambda: backend)
    monkeypatch.setattr(server, "_database_backend", lambda: database)
    balances = SimpleNamespace(list_programs=unavailable, get_balances=unavailable, set_balances=unavailable)
    monkeypatch.setattr(server, "_balances_backend", lambda: balances)
    cards = SimpleNamespace(
        get_cards=lambda owner, include_closed=False: [
            {k: (backend._f(v) if k in {"annual_fee", "msr_amount", "msr_spent"} else v) for k, v in row.items()}
            for row in backend._query(
                "SELECT id, issuer, product, is_business, counts_toward_524, opened_on, closed_on, annual_fee, "
                "bonus_points, bonus_program, msr_amount, msr_deadline, msr_spent, bonus_received_on, notes "
                "FROM cards WHERE owner = %s AND (%s OR closed_on IS NULL) ORDER BY opened_on DESC",
                (owner, include_closed),
            )
        ],
        update_card=unavailable,
    )
    monkeypatch.setattr(server, "_cards_backend", lambda: cards)
    monkeypatch.setattr(server, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", "[]")
