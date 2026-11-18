from datetime import date

import psycopg
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from public_mcp import server

A = "a" * 43
B = "b" * 43
HEADERS = {"Accept": "application/json, text/event-stream"}


def rpc(client, secret, method, params=None):
    return client.post(
        f"/{secret}/mcp",
        headers=HEADERS,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )


def test_balance_tools_are_link_scoped_and_replace_totals(monkeypatch):
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"one":"' + A + '","two":"' + B + '"}')
    backend = server._balances_backend()
    records = {}

    def save(owner, values, as_of):
        records.setdefault(owner, {}).update(values)
        assert as_of == date.today()

    monkeypatch.setattr(backend, "set_balances", save)
    monkeypatch.setattr(backend, "get_balances", lambda owner: records.get(owner, {}))
    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        for secret, amount in [(A, 80000), (B, 500), (A, 70000), (A, 70000)]:
            result = rpc(
                client,
                secret,
                "tools/call",
                {
                    "name": "set_point_balance",
                    "arguments": {"program_code": " CHASE_UR ", "balance": amount},
                },
            ).json()["result"]
            assert not result.get("isError")
            assert "saved" in str(result)
        for secret, amount in [(A, 70000), (B, 500)]:
            result = rpc(
                client,
                secret,
                "tools/call",
                {
                    "name": "get_point_balances",
                    "arguments": {},
                },
            ).json()["result"]
            assert str(amount) in str(result)
            tools = rpc(client, secret, "tools/list").json()["result"]["tools"]
            setter = next(tool for tool in tools if tool["name"] == "set_point_balance")
            assert "owner" not in setter["inputSchema"]["properties"]
            assert setter["annotations"]["readOnlyHint"] is False
    assert records == {"one": {"chase_ur": 70000}, "two": {"chase_ur": 500}}


def test_database_failure_is_sanitized(monkeypatch):
    def fail(*args):
        raise psycopg.OperationalError("private owner secret database details")

    monkeypatch.setattr(server._balances_backend(), "set_balances", fail)
    with pytest.raises(ToolError, match="Could not save points balance") as error:
        server.balance_tools("private")[2]("chase_ur", 1)
    assert "private" not in str(error.value)


def call_tool(monkeypatch, name, arguments):
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"one":"' + A + '"}')
    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        return rpc(client, A, "tools/call", {"name": name, "arguments": arguments}).json()["result"]


def test_balance_validation_reason_reaches_the_model(monkeypatch):
    # The SDK hides plain exception text, so a ValueError would arrive as a bare "Error executing tool".
    def reject(*args):
        raise ValueError("unknown program codes: chase (known: chase_ur)")

    monkeypatch.setattr(server._balances_backend(), "set_balances", reject)
    result = call_tool(monkeypatch, "set_point_balance", {"program_code": "chase", "balance": 1})
    assert result["isError"]
    assert "unknown program codes: chase (known: chase_ur)" in result["content"][0]["text"]


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"opened_on": "2999-01-01"}, "opening date cannot be in the future"),
        ({"product": "4111 1111 1111 1111"}, "never account numbers"),
        ({"annual_fee": "95.001"}, "at most two decimal places"),
    ],
)
def test_card_validation_reason_reaches_the_model(monkeypatch, overrides, reason):
    card = {
        "issuer": "Chase",
        "product": "Sapphire Preferred",
        "opened_on": "2025-03-15",
        "annual_fee": "95",
        "is_business": False,
        "counts_toward_524": True,
    }
    result = call_tool(monkeypatch, "add_portfolio_card", card | overrides)
    assert result["isError"]
    assert reason in result["content"][0]["text"]


@pytest.mark.parametrize(
    ("args", "reason"),
    [
        ({"card_id": -1}, "valid positive card ID"),
        ({"card_id": 1, "annual_fee": "95.001"}, "at most two decimal places"),
        ({"card_id": 1, "opened_on": "2999-01-01"}, "opening date cannot be in the future"),
    ],
)
def test_update_card_validation_reason_reaches_the_model(monkeypatch, args, reason):
    result = call_tool(monkeypatch, "update_portfolio_card", args)
    assert result["isError"]
    assert reason in result["content"][0]["text"]
