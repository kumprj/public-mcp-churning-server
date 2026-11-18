# Public churning MCP

Option 1A: local PostgreSQL/Ollama, Streamable HTTP, secret URLs, Tailscale Funnel.
This adapter uses the sibling `../churning-mcp` package without changing it.
Only the explicit `PUBLIC_TOOLS` allowlist in server.py is registered. Personal
portfolio, transaction, balance and planning tools and arbitrary SQL are excluded.
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
with SELECT grants only on shared corpus/reference tables as defense in depth.

This is a Python ASGI service; moving it later requires hosting Python plus the
database and embedding service. Cloudflare Workers cannot run it unchanged.

## Private portfolio association

`MCP_PORTFOLIO_OWNERS` is an explicit JSON list of secret-map keys allowed to
read their existing portfolio. This installation enables only `kumprj`.
That link exposes `get_portfolio`, filtered by `cards.owner = 'kumprj'` on every
call. Other links cannot list or call that tool. Ownership is captured server-side
and cannot be supplied by the caller. No portfolio writes are enabled.
Keys listed here become stable owner identifiers; rotating their secret preserves
ownership. Restart the server and reconnect clients after changing configuration.
The shared `get_active_offers` tool was removed because it uses the upstream
process-wide owner. Other shared tools remain available.

## Assistant response guidance

MCP initialization instructions ask connected assistants to answer first and then,
when personal context would help, offer a brief optional suggestion to share a card
portfolio. The suggestion is limited to once per conversation and skipped when
the relevant details are already available or the user declines. Links with portfolio
access are instructed to read it first when personal context is needed, distinguish
empty results from errors, and ask only for missing details.

Secret-map keys and values are internal identifiers, never names or greetings.
Instructions use no configured identifiers and tell the assistant to address the
user as “you” unless the user provides a preferred name.

This server currently reads existing portfolios only. Users can share card names,
opening dates, and goals in chat for tailored guidance; the assistant must not
claim to save them. These are instructions to the connected model, not a response
filter or server-side conversation tracker, so client adherence determines wording
and suggestion frequency. Restart the server and reconnect clients to load changes.
# public-mcp-churning-server
# public-mcp-churning-server
