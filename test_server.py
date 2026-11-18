import pytest
from starlette.testclient import TestClient

from server import PUBLIC_TOOLS, create_app

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
    with TestClient(
        create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net"
    ) as client:
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
            result = rpc(client, secret, "tools/list").json()["result"]
            assert {t["name"] for t in result["tools"]} == set(PUBLIC_TOOLS) | {
                "get_portfolio",
                "add_portfolio_card",
            }

        assert client.get("/wrong/mcp").status_code == 404
        assert client.get("/mcp").status_code == 404
        assert rpc(client, A, "tools/list").status_code == 200
        assert (
            client.post(
                f"/{A}/mcp", headers={**HEADERS, "host": "evil.test"}, json={}
            ).status_code
            == 421
        )
    monkeypatch.setenv("MCP_SECRET_SLUGS", '{"bob": "' + B + '"}')
    with TestClient(
        create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net"
    ) as client:
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
    with TestClient(
        create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net"
    ) as client:
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
            assert "at most once per conversation" in instructions
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

    from server import source

    monkeypatch.setenv("MCP_SECRET_SLUGS", json.dumps({"kumprj": A, "friend02": B}))
    monkeypatch.setenv("MCP_PORTFOLIO_OWNERS", '["kumprj"]')

    def query(sql, params):
        assert "owner = %s" in sql
        assert params[0] in {"kumprj", "friend02"}
        return [{"product": params[0] + " card"}]

    monkeypatch.setattr(source, "_query", query)
    with TestClient(
        create_app(funnel_host="example.ts.net"), base_url="https://example.ts.net"
    ) as client:
        tools = rpc(client, A, "tools/list").json()["result"]["tools"]
        portfolio = next(t for t in tools if t["name"] == "get_portfolio")
        assert "owner" not in portfolio["inputSchema"]["properties"]
        assert all(
            t["name"] != "nonexistent_tool"
            for t in rpc(client, B, "tools/list").json()["result"]["tools"]
        )

        def call(secret):
            return rpc(
                client, secret, "tools/call", {"name": "get_portfolio", "arguments": {}}
            ).json()["result"]

        with ThreadPoolExecutor() as pool:
            results = list(pool.map(call, [A, B] * 5))
        for index, result in enumerate(results):
            assert not result.get("isError")
            expected = "kumprj" if index % 2 == 0 else "friend02"
            assert expected + " card" in str(result)


def test_add_card_owner_and_retry(monkeypatch):
    from datetime import date
    from decimal import Decimal
    from server import add_card_tool, db

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
    args = ("Chase", "Test", date(2020, 1, 1), Decimal("95"), False, True)
    assert add_card_tool("first")(*args)["status"] == "saved"
    assert add_card_tool("first")(*args)["status"] == "already_exists"
    assert add_card_tool("second")(*args)["status"] == "saved"
    assert set(saved) == {"first", "second"}
