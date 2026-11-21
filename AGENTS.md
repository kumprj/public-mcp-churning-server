# AGENTS.md

Guidance for AI coding agents working in this repo.

## What this is

A Streamable HTTP MCP adapter that serves the sibling `../churning-mcp` project to chat apps through
per-person secret links (`https://<host>/<secret>/mcp`). It owns no reference data, schema, or migrations;
those live in `churning-mcp`, installed editable via `[tool.uv.sources]` as the optional `backend` extra.

## Layout

| Path | Owns |
|---|---|
| `src/public_mcp/server.py` | `create_app` (secret-link routing, host checks), `PUBLIC_TOOLS` allowlist, owner-scoped portfolio/balance tools, `assistant_instructions`. |
| `src/public_mcp/onboarding.py` | Starter prompts. No credentials or DB access. |
| `tests/conftest.py` | Autouse fixture that mocks the backend and DB; unit tests never touch real data. |
| `server.py`, `src/public_mcp/__main__.py` | Compatibility launchers; prefer `uv run public-mcp`. |

## Commands

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run public-mcp   # serve locally; needs .env (see .env.example)
```

`main` is protected: changes merge only by PR once the `build-and-test` CI check passes. CI installs the built
wheel without the backend, so tests must not import `churning_mcp`.

## Invariants

- **Explicit tool allowlist.** Only `PUBLIC_TOOLS` plus the owner-scoped tools (`get_portfolio`,
  `add_portfolio_card`, `update_portfolio_card`, `list_point_programs`, `get_point_balances`,
  `set_point_balance`) are exposed. Upstream additions appear only once added to `PUBLIC_TOOLS`.
- **Personal data is per owner.** Each secret gets its own registry; owner-scoped tools capture the owner in a
  closure. Never accept an owner from tool input.
- **Secrets stay in `.env`.** Never log or return secret slugs, owner keys, or credentials. Map `psycopg`
  errors to generic `ToolError`s, since raw errors can carry owner names and connection details.

## Adding cards, banks, or offers

Make the change in `../churning-mcp` as a new migration, following "Adding cards, banks, or offers" in its
`AGENTS.md` every time.
