# AGENTS.md

Guidance for AI coding agents working in this repo.

## What this is

A remote (Streamable HTTP) MCP adapter that exposes the sibling `../churning-mcp` project to chat apps through
per-person secret links. It owns no reference data or schema: the card catalog, offers, programs, transfer
partners and migrations all live in `churning-mcp` (installed editable via `[tool.uv.sources]`).

## Layout

| Path | Owns |
|---|---|
| `src/public_mcp/server.py` | App factory, secret-link routing, `PUBLIC_TOOLS` allowlist, per-owner portfolio/balance tools, assistant instructions. |
| `src/public_mcp/onboarding.py` | Starter prompts. No credentials or DB access. |
| `tests/` | `test_server.py`, `test_balances.py`, `test_onboarding.py`. |

## Commands

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Invariants

- **Explicit tool allowlist.** Only names in `PUBLIC_TOOLS` plus the owner-scoped tools are exposed, so upstream
  additions never leak personal data. Each owner gets a separate registry.
- **Personal data is per owner.** Portfolio and balance tools are bound to the link's owner; never accept an
  owner from tool input.
- **Secrets stay in `.env`.** Never log or return secret slugs, owner keys, or credentials.

## Adding cards, banks, or offers

Card data changes belong in `../churning-mcp` as a new migration, not here. Follow "Adding cards, banks, or
offers" in `../churning-mcp/AGENTS.md`, which requires every time: card information, annual fees (with fee
history), approval rules, current and highest-ever offers, and other facts (downgrade paths, transfer partners,
legacy versions, dated upcoming changes). A new upstream tool only appears on public links once it is added to
`PUBLIC_TOOLS`.
