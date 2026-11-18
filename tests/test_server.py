import pytest
from starlette.testclient import TestClient

from public_mcp.server import PUBLIC_TOOLS, create_app

A = "a" * 43
B = "b" * 43
HEADERS = {"Accept": "application/json, text/event-stream"}


def rpc(client, secret, method, params=None):
    return client.post(
        f"/{secret}/mcp",
        headers=HEADERS,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )


def test_links_and_tools(monkeypatch):
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", "[]")
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '", "bob": "' + B + '"}')
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        for secret in (A, B):
            response = rpc(
                client,
                secret,
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            )
            assert response.status_code == 200
            assert "prompts" in response.json()["result"]["capabilities"]
            assert len(rpc(client, secret, "prompts/list").json()["result"]["prompts"]) == 4
            result = rpc(client, secret, "tools/list").json()["result"]
            assert {t["name"] for t in result["tools"]} == set(PUBLIC_TOOLS) | {
                "get_portfolio",
                "add_portfolio_card",
                "update_portfolio_card",
                "list_point_programs",
                "get_point_balances",
                "set_point_balance",
            }

        assert client.get("/wrong/mcp").status_code == 404
        assert client.get("/mcp").status_code == 404
        assert rpc(client, A, "tools/list").status_code == 200
        assert client.post(f"/{A}/mcp", headers={**HEADERS, "host": "evil.test"}, json={}).status_code == 421
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"bob": "' + B + '"}')
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        assert rpc(client, A, "tools/list").status_code == 404
        assert rpc(client, B, "tools/list").status_code == 200


@pytest.mark.parametrize("value", ["{}", "[]", '{"a":"short"}', "invalid"])
def test_invalid_secrets(monkeypatch, value):
    monkeypatch.setenv("MCP_SECRET_SLUGS", value)
    with pytest.raises(ValueError):
        create_app(funnel_host="example.ts.net")


def test_assistant_guidance_and_private_labels(monkeypatch):
    import json

    owners = {"private-owner-label": A, "private-friend-label": B}
    monkeypatch.setenv("MCP_SECRET_SLUGS", json.dumps(owners))
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", '["private-owner-label"]')
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        for secret in (A, B):
            response = rpc(
                client,
                secret,
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            )
            assert response.status_code == 200
            instructions = response.json()["result"]["instructions"]
            assert "Answer the user's question first" in instructions
            assert "at most once per conversation and never more" in instructions
            assert "Never use MCP_SECRET_SLUGS keys or values" in instructions
            assert "use add_portfolio_card" in instructions
            if secret == A:
                assert "Use get_portfolio" in instructions
                assert "a tool error does not mean" in instructions
            else:
                assert "Use get_portfolio" in instructions
            metadata = response.text + rpc(client, secret, "tools/list").text
            for private_value in (*owners.keys(), *owners.values()):
                assert private_value not in metadata


def test_portfolio_isolation(monkeypatch):
    import json
    from concurrent.futures import ThreadPoolExecutor

    from public_mcp.server import _research_backend

    source = _research_backend()

    monkeypatch.setenv("MCP_SECRET_SLUGS", json.dumps({"kumprj": A, "friend02": B}))
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", '["kumprj"]')

    def query(sql, params):
        assert "owner = %s" in sql
        assert params[0] in {"kumprj", "friend02"}
        return [{"product": params[0] + " card"}]

    monkeypatch.setattr(source, "_query", query)
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        tools = rpc(client, A, "tools/list").json()["result"]["tools"]
        portfolio = next(t for t in tools if t["name"] == "get_portfolio")
        assert "owner" not in portfolio["inputSchema"]["properties"]
        assert all(t["name"] != "nonexistent_tool" for t in rpc(client, B, "tools/list").json()["result"]["tools"])

        def call(secret):
            return rpc(client, secret, "tools/call", {"name": "get_portfolio", "arguments": {}}).json()["result"]

        with ThreadPoolExecutor() as pool:
            results = list(pool.map(call, [A, B] * 5))
        for index, result in enumerate(results):
            assert not result.get("isError")
            expected = "kumprj" if index % 2 == 0 else "friend02"
            assert expected + " card" in str(result)


def test_add_card_owner_and_retry(monkeypatch):
    from datetime import date
    from decimal import Decimal

    from public_mcp.server import _database_backend, add_card_tool

    db = _database_backend()

    saved = {}

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, sql, params):
            self.result = None
            if sql.startswith("SELECT id"):
                self.result = saved.get(params[0])
            elif sql.startswith("INSERT"):
                self.result = {"id": len(saved) + 1, "product": params[2]}
                saved[params[0]] = self.result
            return self

        def fetchone(self):
            return self.result

    monkeypatch.setattr(db, "connect", lambda **kwargs: Connection())
    args = ("Chase", "Test", date(2020, 1, 1), Decimal(95), False, True)
    assert add_card_tool("first")(*args)["status"] == "saved"
    assert add_card_tool("first")(*args)["status"] == "already_exists"
    assert add_card_tool("second")(*args)["status"] == "saved"
    assert set(saved) == {"first", "second"}


def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '"}')
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_update_portfolio_card_success_and_opened_on(monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from public_mcp import server

    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '"}')
    cards_mock = SimpleNamespace()
    updated = {}

    def mock_update(owner, card_id, annual_fee=None, notes=None, closed_on=None, opened_on=None):
        assert owner == "alice"
        record = {
            "id": card_id,
            "annual_fee": annual_fee,
            "notes": notes,
            "closed_on": closed_on,
            "opened_on": opened_on,
        }
        updated[card_id] = record
        return record

    cards_mock.update_card = mock_update
    monkeypatch.setattr(server, "_cards_backend", lambda: cards_mock)

    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        res = rpc(
            client,
            A,
            "tools/call",
            {
                "name": "update_portfolio_card",
                "arguments": {
                    "card_id": 10,
                    "annual_fee": "250.00",
                    "notes": "Kept with retention offer",
                    "closed_on": "2026-11-01",
                    "opened_on": "2023-03-01",
                },
            },
        ).json()["result"]
        assert not res.get("isError")
        assert updated[10]["annual_fee"] == 250.0
        assert updated[10]["notes"] == "Kept with retention offer"
        assert updated[10]["closed_on"] == date(2026, 11, 1)
        assert updated[10]["opened_on"] == date(2023, 3, 1)


def test_update_portfolio_card_validation(monkeypatch):
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '"}')
    with TestClient(create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        # Invalid card_id
        res_id = rpc(
            client,
            A,
            "tools/call",
            {"name": "update_portfolio_card", "arguments": {"card_id": 0}},
        ).json()["result"]
        assert res_id["isError"]
        assert "valid positive card ID" in res_id["content"][0]["text"]

        # Invalid annual_fee decimal places
        res_fee = rpc(
            client,
            A,
            "tools/call",
            {"name": "update_portfolio_card", "arguments": {"card_id": 1, "annual_fee": "95.555"}},
        ).json()["result"]
        assert res_fee["isError"]
        assert "at most two decimal places" in res_fee["content"][0]["text"]

        # Future opened_on
        res_future = rpc(
            client,
            A,
            "tools/call",
            {"name": "update_portfolio_card", "arguments": {"card_id": 1, "opened_on": "2999-01-01"}},
        ).json()["result"]
        assert res_future["isError"]
        assert "opening date cannot be in the future" in res_future["content"][0]["text"]


def test_update_portfolio_card_owner_sanitization(monkeypatch):
    from types import SimpleNamespace

    from public_mcp import server

    secret_owner = "super_secret_owner_key_xyz"
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"' + secret_owner + '": "' + A + '"}')
    cards_mock = SimpleNamespace()

    def mock_update(owner, card_id, **kwargs):
        raise ValueError(f"Card {card_id} not found in {owner}'s portfolio")

    cards_mock.update_card = mock_update
    monkeypatch.setattr(server, "_cards_backend", lambda: cards_mock)

    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        res = rpc(
            client,
            A,
            "tools/call",
            {"name": "update_portfolio_card", "arguments": {"card_id": 999}},
        ).json()["result"]
        assert res["isError"]
        text = res["content"][0]["text"]
        assert "Card 999 not found in portfolio" in text
        assert secret_owner not in text


def test_update_portfolio_card_database_error_sanitization(monkeypatch):
    from types import SimpleNamespace

    import psycopg

    from public_mcp import server

    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '"}')
    cards_mock = SimpleNamespace()

    def mock_update(owner, card_id, **kwargs):
        raise psycopg.OperationalError("private database credentials and host leak")

    cards_mock.update_card = mock_update
    monkeypatch.setattr(server, "_cards_backend", lambda: cards_mock)

    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        res = rpc(
            client,
            A,
            "tools/call",
            {"name": "update_portfolio_card", "arguments": {"card_id": 1, "annual_fee": "95.00"}},
        ).json()["result"]
        assert res["isError"]
        text = res["content"][0]["text"]
        assert "Could not update the card. Please try again later." in text
        assert "private" not in text


def test_get_portfolio_database_failure_is_sanitized(monkeypatch):
    from types import SimpleNamespace

    import psycopg

    from public_mcp import server

    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"alice": "' + A + '"}')
    cards_mock = SimpleNamespace()

    def mock_get(owner, include_closed=False):
        raise psycopg.OperationalError("private postgres credentials leak")

    cards_mock.get_cards = mock_get
    monkeypatch.setattr(server, "_cards_backend", lambda: cards_mock)

    with TestClient(server.create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net") as client:
        res = rpc(
            client,
            A,
            "tools/call",
            {"name": "get_portfolio", "arguments": {}},
        ).json()["result"]
        assert res["isError"]
        text = res["content"][0]["text"]
        assert "Could not read saved cards. Please try again later." in text
        assert "private" not in text
