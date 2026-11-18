# Public churning MCP

Option 1A: local PostgreSQL/Ollama, Streamable HTTP, secret URLs, Tailscale Funnel.
This adapter uses the sibling `../churning-mcp` package without changing it.
Only the explicit `PUBLIC_TOOLS` allowlist in server.py is registered. Personal
transaction, balance and planning tools and arbitrary SQL are excluded. Portfolio
read/add tools are registered separately for each link.
Existing tools retain their PostgreSQL read-only connections.

## Setup (PowerShell, from this folder)

```powershell
uv sync
Copy-Item .env.example .env
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
tailscale status
```

Edit `.env`: set DATABASE_URL to the existing database connection, FUNNEL_HOST to
this desktop's full Tailscale DNS hostname (no scheme or path), and set secrets.
Keep CHURNING_OWNER=public-unused: the upstream settings require it, but public
tools do not use a personal owner. Configure Ollama as in the source project.
Do not copy SMTP credentials or other unrelated private settings.

For separate friend links use a JSON object, wrapped in single quotes in `.env`:

```dotenv
MCP_SECRET_SLUGS='{"alice":"GENERATE_A_UNIQUE_43_CHARACTER_SECRET_HERE","bob":"GENERATE_ANOTHER_UNIQUE_43_CHARACTER_SECRET"}'
```

Generate a fresh secret for every entry using the command above. Names are local
labels, not URL components. MCP_SECRET_SLUGS takes precedence over the legacy
single MCP_SECRET_SLUG. Empty/invalid/duplicate secrets prevent startup.
Each URL is `https://<FUNNEL_HOST>/<that-friends-secret>/mcp`.
Remove a friend's entry and restart to revoke it. Existing sessions are stateless;
old links then return 404. All links grant the same shared research capabilities.
Anyone with a link can use it; it is a credential, not proof of user identity.

## Run and expose

```powershell
uv run --no-sync python server.py
```

In a second terminal, after configuring Tailscale Funnel permissions:

```powershell
tailscale funnel --bg 8000
tailscale funnel status
```

See https://tailscale.com/docs/reference/tailscale-cli/funnel for Funnel setup and
controls. Inspect existing Funnel/Serve routes before changing them. The desktop
and Python process must remain running. Funnel's background flag only persists
the tunnel, not the Python server. To stop this Funnel listener use
`tailscale funnel --https=443 off` (affects that listener).

Paste a friend's full secret URL into a client supporting remote Streamable HTTP
MCP. Client availability varies; this service does not implement OAuth.
Uvicorn access logging is disabled. Do not enable request URL logging in proxies
or share screenshots of links. Host/Origin checks allow only the configured host
and local development addresses. No public tunnel is enabled automatically.

## Verification

```powershell
uv run pytest -q
uv run ruff check .
```

Tests exercise the actual HTTP MCP initialize and tools/list protocol for two
links, revoked/unknown paths, host validation, and invalid configuration without
requiring your database. Live database queries and external Funnel connectivity
must be checked after configuring `.env`. For production, use a database role
with SELECT grants on shared tables and the portfolio grants described below.

This is a Python ASGI service; moving it later requires hosting Python plus the
database and embedding service. Cloudflare Workers cannot run it unchanged.

## Portfolio tools and conversation suggestions

Every secret link now exposes `get_portfolio` and `add_portfolio_card`. Cards are
stored under the corresponding MCP_SECRET_SLUGS dictionary key in `cards.owner`.
Ownership is fixed server-side and cannot be supplied by callers. Keys and tokens
are internal identifiers, never greetings. Anyone with a link can read and add its
cards; rotating a secret preserves ownership when its key stays unchanged.

| Task | Command or example | Behavior |
| --- | --- | --- |
| Install | `uv sync` | Uses sibling `../churning-mcp`. |
| Generate secret | `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"` | Generate a unique secret for each friend. |
| Configure friend | `MCP_SECRET_SLUGS` maps a stable owner key to a generated secret in `.env`. | Every configured link gets portfolio tools. |
| Start/restart | `uv run --no-sync python server.py` | Stop the previous process first; reconnect clients afterward. |
| Connect | `https://<FUNNEL_HOST>/<secret>/mcp` | Opens that friend's tools. |
| Add card | Add my Chase Sapphire Preferred, opened 2025-03-15, annual fee $95, personal card reporting to personal credit. | Saves the card under the link's owner. |
| Add portfolio | Add these cards to my portfolio: ... | Asks for missing details and saves each card separately. |
| Review | What cards are in my portfolio? | Reads this link's cards only. |
| Personalize | Which card should I consider next based on my portfolio? | Reads cards before combining them with shared research. |
| Suggestion | Consider adding your card portfolio so I can tailor this guidance to the cards you already have. | Answer first, suggest only when helpful, at most once per conversation. |
| Check | `uv run pytest -q` and `uv run ruff check .` | Local verification. |

Required fields: issuer, product, opening date, annual fee, business status, and
personal-credit reporting status for 5/24. Missing details must not be guessed.
Same issuer/product (case-insensitive) and opening date returns the existing card;
retries do not overwrite records. Saves are serialized per owner in this adapter.
Updates and deletions currently require database edits. Each card commits separately.

Use the existing upstream schema including the owner migration; no new migration
is required. The database role needs SELECT and INSERT on cards and USAGE on its
id sequence. Shared research connections remain read-only. The legacy
MCP_PORTFOLIO_OWNERS list no longer gates access; listed keys must still exist.

The assistant uses 'you' unless a preferred name is supplied, avoids repeating
suggestions, checks existing cards before requesting a portfolio, and reports saved
cards only after a successful write. These are model instructions, so client
adherence determines wording and frequency. Never submit account numbers or secrets.
