"""Public CI tests exercise real MCP discovery without the private research backend."""

import pytest
from mcp.server import MCPServer
from starlette.testclient import TestClient

from public_mcp.onboarding import STARTER_PROMPTS, register_starter_prompts


def rpc(client, method, params=None):
    response = client.post(
        "/mcp",
        headers={"Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def client():
    server = MCPServer("onboarding-test")
    register_starter_prompts(server)
    with TestClient(
        server.streamable_http_app(stateless_http=True, json_response=True),
        base_url="http://localhost:8000",
    ) as connection:
        yield connection


def test_prompt_discovery(client):
    initialized = rpc(
        client,
        "initialize",
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    )
    assert "prompts" in initialized["result"]["capabilities"]
    prompts = rpc(client, "prompts/list")["result"]["prompts"]
    assert {prompt["name"] for prompt in prompts} == set(STARTER_PROMPTS)
    assert all(not prompt.get("arguments") for prompt in prompts)


@pytest.mark.parametrize("name", STARTER_PROMPTS)
def test_prompt_retrieval(client, name):
    messages = rpc(client, "prompts/get", {"name": name})["result"]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"]["text"] == STARTER_PROMPTS[name][1]
    if name == "build_portfolio":
        assert "lookup_card_details" in messages[0]["content"]["text"]
        assert "update_portfolio_card" in messages[0]["content"]["text"]


def test_unknown_prompt(client):
    assert "error" in rpc(client, "prompts/get", {"name": "unknown"})
