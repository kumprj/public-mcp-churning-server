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
    monkeypatch.setattr(server, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", "[]")
