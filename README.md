# Public Churning MCP

Get credit card rewards guidance that takes the cards you already hold into account.
Connect this service to your AI app, tell the assistant about your cards, and ask it
to save your portfolio. It can then use those details when you ask about your next
card, annual fees, bonuses, or rewards.

Without your portfolio, answers are based on general research and what you share in
the current conversation. With a saved portfolio, the assistant can check your
existing cards, opening dates, and fees before answering. This helps it avoid
suggesting a card you already have and identify missing information relevant to
eligibility or value. It does not guarantee approval or bonus eligibility.

**Hosted access is available upon request for now.** Contact the maintainer through
the channel where you learned about this project to request a private connection
link. There is no self-service signup. Never post connection URLs or personal card
details in public issues.

With a hosted connection, you do not need to install Python or run a server. Add the
link to your app, then start a conversation using the examples below.

## Recommended Getting Started Flow

1. Request access and receive your private connection URL.
2. Add the URL to an app supporting remote Streamable HTTP MCP connections
   (see [Supported apps](#supported-apps-including-ios)).
3. Send: **Help me add my cards to my portfolio so you can tailor your answers to me.**
   You can also select **Set up my portfolio** from the app's MCP prompt picker.
4. List your cards in ordinary language. Start with whatever you know; the assistant
   will ask for missing details before saving each card.
5. Ask **Show me my saved portfolio** and check that the cards and details are correct.
   The assistant should confirm a save only after it succeeds.
6. Ask **Based on my saved portfolio, which card should I consider next?** Add your
   goal, such as cash back or a planned trip, so the answer can be more useful.

### Supported apps, including iOS

Any app that supports custom remote MCP connectors can use your connection URL.
Paste the full URL exactly as you received it; it already contains your private
access link, so no extra sign-in or token is needed.

| App | Custom remote MCP support | Plan required | Where to add the URL |
| --- | --- | --- | --- |
| Claude | Yes, natively in the iOS app and synced across devices | Free includes 1 custom connector; unlimited on Pro, Max, Team, and Enterprise | In the Claude iOS app, web, or desktop: **Customize → Connectors → Add custom connector**. |
| Gemini | Yes, added on the web and synced to iOS | Free for personal Google accounts in the US, 18+, with **Keep Activity** on | In a browser at gemini.google.com: **Settings → Connected Apps → Add a custom app**. It then appears in the iOS app. |
| ChatGPT | Yes, as plugins/MCP apps, synced to iOS | Paid or workspace plans; not consumer Free | On the web at chatgpt.com: **Settings → Plugins → Add custom MCP server**. Then use it in mobile chats. |
| Perplexity | Yes, as custom remote connectors | Paid plans (Pro, Max, Enterprise); not Free | On the web or desktop: **Account Settings → Connectors**. Synced across your account. |
| Third-party iOS MCP clients | Yes, as full native MCP clients | Free, using your own AI provider API key | App Store clients such as ChatMCP or Joey MCP Client let you add custom MCP URLs directly on your phone. |

On iOS, Claude is the simplest option because you can paste the URL right in the
app, and the free plan covers one custom connector. Gemini is the best free
alternative where it is available. ChatGPT and Perplexity work if you already pay
for them, but you add the URL in a web browser first.

This table reflects availability as of November 2026. Plans, regions, and menu
names change often, so check each app's current help pages before choosing one.

### What to tell the assistant

You do not need to fill out a form or know a tool command. For example:

> I'd like to add my portfolio. I have a Chase Sapphire Preferred and an Amex Gold.
> Walk me through the details you need, save my cards, then show me what was saved.

For each card, the assistant needs:

| Detail | Why it helps |
| --- | --- |
| Issuer and card name | Identifies what you already hold. |
| Opening date | Provides context for application timing and account history. |
| Annual fee | Helps evaluate the cost of keeping a card. |
| Personal or business card | Helps distinguish card types and relevant rules. |
| Whether it reports to personal credit | Provides context for Chase 5/24 counting. |

If you do not know a detail, say so. The assistant should help you identify what to
check rather than invent a value. An incomplete card cannot be saved until its
required details are supplied. Never provide full card numbers, security codes,
passwords, or account credentials.

### After your portfolio is saved

Your cards are associated with your private connection and remain available in
future conversations using that connection. You can say:

| Ask the assistant | How your portfolio helps |
| --- | --- |
| Given my cards, what should I consider next for a hotel trip? | Grounds research in your existing cards, then asks about your travel goals. |
| Help me evaluate whether my annual fees are worth paying. | Starts with saved fees and asks which benefits you actually use. |
| What else do you need to assess my eligibility for this bonus? | Uses saved account history and identifies missing facts rather than assuming eligibility. |
| Show my saved cards, then help me add a new one. | Reviews existing entries before saving another card. |

Saving cards does not automatically provide balances, spending history, benefit
usage, or past bonus details. Share relevant context when asked. Goals and spending
preferences help within the conversation but are not saved by this service.
If a saved card needs correcting or removing, contact the maintainer; chat-based
editing and deletion are not currently available.

### Other ways to get started

You can ask research questions immediately; portfolio setup is optional. Connecting
alone does not send a chat message. The app controls whether it displays MCP prompts.
The getting-started prompt requests a brief welcome once in the current conversation;
there is no cross-session welcome tracker or automatic welcome on connection.

| Starter prompt | Copy-and-paste alternative | Purpose |
| --- | --- | --- |
| `getting_started` | Help me get started with card rewards research. | Offers portfolio setup, next-card research, or redemption analysis. |
| `build_portfolio` | Help me add my cards to my portfolio. | Checks saved cards and collects missing entry details. |
| `next_card` | Based on my portfolio, which card should I consider next? | Combines saved cards, your goals, and relevant research. |
| `evaluate_redemption` | Help me compare this points redemption with paying cash. | Collects prices, points, and fees to evaluate the tradeoff. |

Example card entry:

> Add my Chase Sapphire Preferred, opened 2025-03-15, annual fee $95, a personal
> card that reports to personal credit.

The assistant is instructed to answer first and suggest adding a portfolio only when
useful, at most once per conversation. It uses existing card details before requesting
them again. Wording and tool approvals depend on the app and model.

## Capabilities

Shared research covers offers, points valuations, data points, booking windows,
offer history, retention, and reconsideration. `get_portfolio` reads the connection's
cards; `add_portfolio_card` saves cards explicitly supplied by the user.

Matching issuer, product, and opening date returns the existing card without changing
it. Issuer and product matching is case-insensitive. Saves through this adapter are
serialized per owner. Each card commits separately, so a later failure does not undo
earlier additions. Updates and deletions currently require administrative database edits.

## Self-hosting

This repository contains the HTTP adapter and starter prompts. The research backend,
database schema, and ingestion pipeline live in the separate private `churning-mcp`
repository. Self-hosting requires authorized access to that backend.

Requirements: Python 3.12+, `uv`, the private backend at `../churning-mcp`, its PostgreSQL
schema (including the owner migration), research data, and its embedding service.
Follow backend documentation for migrations, ingestion, and embeddings. This adapter
does not populate the research database on startup.

From this repository, using PowerShell:

```powershell
uv sync --extra backend
Copy-Item .env.example .env
uv run --no-sync python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Generate one secret per user. Configure `.env` using generated values in place of
these placeholders:

```dotenv
MCP_SECRET_SLUGS='{"user-one":"<generated-secret>","user-two":"<another-generated-secret>"}'
FUNNEL_HOST=your-host.example.ts.net
PORT=8000
CHURNING_OWNER=public-unused
```

| Setting | Purpose |
| --- | --- |
| `MCP_SECRET_SLUGS` | JSON map of stable owner keys to unique secrets; takes precedence over `MCP_SECRET_SLUG`. |
| `MCP_SECRET_SLUG` | Legacy single-link secret, using owner key `single`. |
| `FUNNEL_HOST` | Public hostname without scheme, port, or path; used for host and origin validation. |
| `PORT` | Local HTTP port, default `8000`. |
| `DATABASE_URL` | Upstream PostgreSQL connection string. |
| `CHURNING_OWNER` | Required upstream setting; use `public-unused`. Ownership is captured separately per connection. |
| `OLLAMA_HOST` | Upstream embedding service address. |
| `EMBED_MODEL` | Embedding model matching the research index. |
| `MCP_PORTFOLIO_OWNERS` | Legacy validation list, normally `[]`. All configured links have portfolio access; listed keys must still exist. |

Secrets must be unique, URL-safe strings of 32-128 characters. The database role needs
SELECT on research tables, SELECT and INSERT on `cards`, and USAGE on its ID sequence.
Research tools use read-only connections.

Start the service:

```powershell
uv run --no-sync public-mcp
```

It binds to `127.0.0.1`. For Tailscale Funnel, configure Funnel access and expose the
local port from a second terminal:

```powershell
tailscale funnel --bg 8000
tailscale funnel status
```

Use your configured port if different. See the
[Tailscale Funnel documentation](https://tailscale.com/docs/reference/tailscale-cli/funnel)
for deployment requirements. The host and Python process must remain running.
Give each user their corresponding URL: `https://<FUNNEL_HOST>/<secret>/mcp`.
The service does not implement OAuth. Reconnect clients after server changes to
refresh tools, prompts, and instructions.

| Operation | Command or action |
| --- | --- |
| Start | `uv run --no-sync public-mcp` |
| Restart | Stop the existing process, then start it again. |
| Check tunnel | `tailscale funnel status` |
| Stop Funnel HTTPS listener | `tailscale funnel --https=443 off` (affects that listener). |
| Rotate access | Replace the secret value, restart, and distribute the new URL. Keep its owner key unchanged. |
| Revoke access | Remove the map entry and restart. Saved cards are retained. |
| Unit tests | `uv run pytest -q` (private backend calls are mocked). |
| Build package | `uv build` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |

## Access and data isolation

The map key is stored in `cards.owner`. Ownership is fixed server-side; callers cannot
choose another owner. Keys and secrets are internal identifiers, and assistant
instructions prohibit using them as names or greetings.

A URL is a bearer credential: anyone holding it can read and add cards for its owner.
Preserve owner keys when rotating secrets and do not reassign an existing key to a
different person. Keep `.env`, data, and private URLs out of this public repository.
Access logging is disabled; avoid recording secret URLs in proxies. Host and origin
validation is enabled.

Research tools use the explicit `PUBLIC_TOOLS` allowlist. Upstream personal transaction,
balance, and planning tools are excluded. Personalized answers combine the scoped
portfolio read with shared research.

## Contributing and CI

`main` is protected: changes merge only through pull requests, and the
`build-and-test` check from GitHub Actions must pass on a branch that is up to date
with `main`. These rules apply to administrators too. Direct pushes, force pushes,
and branch deletion are blocked. Reviewer approval is not required.

The GitHub Action builds a wheel and source distribution, installs the wheel, and
runs the unit suite. It needs no private credentials and can run on fork pull requests.
Tests use the real MCP SDK with mocked research/database boundaries. They do not
exercise the private backend implementation or a live database.
Live database permissions and tunnel connectivity require separate deployment checks.

```text
src/public_mcp/       # Installable package: HTTP service and starter prompts
tests/               # Unit tests and isolated backend fixtures
.github/workflows/   # GitHub Actions build and unit tests
pyproject.toml       # Dependencies, CLI, build, and test configuration
server.py            # Compatibility launcher for existing deployments
```

The `public-mcp` CLI and `python -m public_mcp` both start the service. Run from the
directory containing your `.env`. The optional `backend` extra installs the private
sibling package for runtime use; public wheel installation and unit tests do not
require it. `uv` resolves the local backend source when managing the development
environment, so keep the sibling checkout available when using the supplied lockfile.

Keep backend implementation, operational data, and private deployment details in the
private `churning-mcp` repository. Never attach secrets to public issues or PRs.
