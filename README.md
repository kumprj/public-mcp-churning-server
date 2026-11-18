# Public Churning MCP

Credit card rewards guidance that accounts for the cards you already have. Connect
this MCP server to your AI app, tell the assistant about your cards, and it will use
them when you ask about your next card, annual fees, bonuses, or rewards.

Without a saved portfolio, answers rely on general research and what you say in the
conversation. With one, the assistant checks your cards, opening dates, and fees
first, so it won't suggest a card you already have and can point out missing
eligibility details. It can't guarantee approval or bonuses.

**MCP access is available upon request. General availability is coming soon after
the beta period.** Ask the maintainer for a private connection link through the
channel where you found this project. There's nothing to install. Never post your
link or card details in public issues.

## Getting started

1. Get your private connection URL.
2. Add it to a [supported app](#supported-apps). Paste the whole URL; there's no
   separate sign-in.
3. Say: **Help me add my cards to my portfolio.**
4. Describe your cards in plain language. Ballpark answers are fine, and the
   assistant will ask for anything missing.
5. Say **Show me my saved portfolio** to check what was saved.
6. Ask **Which card should I consider next?** and mention your goal, such as cash
   back or an upcoming trip.

### Supported apps

| App | Plan required | Where to add the URL |
| --- | --- | --- |
| Claude | Free includes 1 custom connector; unlimited on Pro, Max, Team, and Enterprise | In the iOS app, web, or desktop: **Customize → Connectors → Add custom connector** (hit **Next**, leave **No Sign In** set, and you're all set!) |
| Gemini | Free for personal Google accounts in the US, 18+, with **Keep Activity** on | On the web at gemini.google.com: **Preferences → Skills → Connectors tab** (just paste the URL and accept; it then appears on iOS) |
| ChatGPT / Codex | Paid or workspace plans (Plus, Team, Enterprise) | On the web at chatgpt.com: **Settings → Connectors / Developer Mode → Add custom MCP server** (paste URL, set authentication to None); then active across web and mobile |
| Perplexity | Pro, Max, or Enterprise | On the web or desktop: **Account Settings → Connectors → Add Connector** (paste URL); synced across your account |
| Muse | Free with Meta account | In Muse web or app: **Settings → Connectors** (or prompt Muse in chat to build a custom connector; see message below) |
| Third-party iOS MCP clients | Free, using your own AI provider API key | Add the URL in apps such as ChatMCP or Joey MCP Client |

On iOS, Claude is the simplest: you paste the URL right in the app, and the free plan
covers it. Gemini and Muse are great free alternatives where available. ChatGPT and
Perplexity need a paid plan and a web browser for setup. This reflects November 2026;
plans and menus change, so check each app's help pages.

### Getting started with the Churning MCP: How to talk to it successfully

Once connected, talk to the assistant naturally—no special syntax, forms, or code are required.

#### App-specific tips to talk to it successfully
- **Claude:** Ensure the **Churning** connector toggle is enabled in your chat bar. You can choose a starter prompt if visible or simply start typing.
- **Gemini:** Ensure the connector is active under **Preferences → Skills → Connectors**. It works across both web and iOS; if Gemini doesn't automatically trigger the tool on a broad question, explicitly prompt it: *"Check my Churning portfolio"* or *"Use the Churning tool."*
- **ChatGPT / Codex:** Ensure the custom MCP server is enabled in your chat session. Mentioning `@Churning` or prompting *"Use the Churning tool to check my portfolio"* ensures the model routes directly to the MCP tools rather than relying on general browsing.
- **Perplexity:** Verify that Connectors are active in your thread sources/focus toggle. Frame requests clearly around your cards, e.g., *"Using my Churning connector, what card should I apply for next?"*
- **Muse:** Verify the connector is toggled on in **Settings → Connectors**. To set up the custom connector in Muse chat, send:
  > "Build a custom connector for Churning using the remote MCP server at <sample URL here>. This URL is publicly hosted over the internet via Tailscale Funnel—connect directly over public HTTPS without requesting a Tailnet device invite. It uses Streamable HTTP transport and requires no separate API key or auth header because authentication is embedded in the URL path. Connect to the existing server without creating a local replacement, list the available tools, and save this connector for future chats."
  
  When prompted on the secure credentials page, enter only the secret token from the URL path. Once saved, you can converse normally or prompt: *"Using my Churning connector, check my portfolio and see if I'm eligible for this bonus."*

#### Conversational examples

Speak in plain English. For example:

> I have a Chase Sapphire Preferred I opened around March 2023 and an Amex Gold from
> last year. Walk me through what you need, save them, and show me what was saved.

#### Suggested card details (ballpark dates and details are fine)

The assistant factors in five key details when saving cards and checking rules such as Chase 5/24:

| Detail | Why it helps |
| --- | --- |
| Issuer and card name | Identifies what you already have. |
| Opening date | Timing rules such as Chase 5/24 depend on it. "Around March 2023" or "2023" works. |
| Annual fee | Shows what each card costs to keep. A rough figure is fine. |
| Personal or business | Different rules apply to each. |
| Reports to personal credit | Decides whether a card counts toward 5/24. If you're unsure, the assistant can tell you what's typical. |

An approximate date is saved as the first of that month (January 1 for a year alone),
and the assistant tells you it's an estimate. Closer answers mean more accurate
guidance, especially on timing rules.

You can skip a card, or setup entirely, and still ask questions; answers will just be
less personal. A saved card needs all five details, so mention any card you can't
estimate in the conversation instead. Never share card numbers, security codes,
passwords, or logins.

### Points balances

Say **Save my Chase Ultimate Rewards balance as 80,000 points.** A new amount replaces
the old one, and the assistant notes when each balance was recorded. These are numbers
you report, not a live connection to your accounts.

### Using your portfolio

Saved cards and balances stay with your connection across conversations. Try:

| Ask | How your portfolio helps |
| --- | --- |
| Given my cards, what should I get next for a hotel trip? | Starts from your cards, then asks about your trip. |
| Are my annual fees worth paying? | Starts from your saved fees and asks which benefits you use. |
| What else do you need to check my eligibility for this bonus? | Uses your card history and names the missing facts. |
| Show my saved cards, then help me add a new one. | Reviews what's saved before adding more. |

Goals, spending, and benefit usage aren't saved, so share them when asked. To correct
or remove a saved card, contact the maintainer.

### Ways to start a conversation

Connecting doesn't send a message, and you can ask research questions right away. Most
people just type one of these:

| Type this | Or pick from the prompt menu | What happens |
| --- | --- | --- |
| Help me get started with card rewards research. | Get started | A brief welcome, then a choice of what to do next. |
| Help me add my cards to my portfolio. | Set up my portfolio | Checks saved cards, then collects new ones. |
| Based on my portfolio, which card should I consider next? | Explore my next card | Combines your cards, goals, and current research. |
| Help me compare this points redemption with paying cash. | Evaluate a points redemption | Collects prices, points, and fees to compare. |

Some apps show a prompt menu for the connection; many mobile apps don't. A menu item
sends a longer, prewritten version of the same request, which can be slightly more
consistent, but typing works just as well.

The assistant answers your question first and suggests adding a portfolio only when
it would help: at most once per conversation, and not after you decline.

## Tools

Shared research covers offers, point valuations, data points, award booking windows,
offer history, retention, and reconsideration.

| Tool | Purpose |
| --- | --- |
| `get_portfolio` | Reads this connection's cards. |
| `add_portfolio_card` | Saves a card the user supplies. A matching issuer, product, and opening date (case-insensitive) returns the existing card unchanged. Saves are serialized per owner and commit one card at a time. |
| `get_point_balances` | Reads this connection's points totals and their dates. |
| `set_point_balance` | Replaces one program's total; rejected if a newer-dated balance exists. |
| `list_point_programs` | Lists supported program codes. |

Starter prompts: `getting_started`, `build_portfolio`, `next_card`,
`evaluate_redemption`. Card edits and deletions require a database administrator.

## Self-hosting

This repository is the HTTP adapter. The research backend, database schema, and
ingestion pipeline live in the private `churning-mcp` repository, so self-hosting
requires access to it.

Requirements: Python 3.12+, `uv`, the backend checked out at `../churning-mcp`, its
PostgreSQL schema and research data, and its embedding service. See the backend docs
for migrations, ingestion, and embeddings; this adapter doesn't populate the database.

```bash
uv sync --extra backend
cp .env.example .env
uv run --no-sync python -c "import secrets; print(secrets.token_urlsafe(32))"  # one per user
```

Fill in `.env`:

```dotenv
MCP_SECRET_SLUGS='{"user-one":"<generated-secret>","user-two":"<another-generated-secret>"}'
FUNNEL_HOST=your-host.example.ts.net
PORT=8000
CHURNING_OWNER=public-unused
```

| Setting | Purpose |
| --- | --- |
| `MCP_SECRET_SLUGS` | JSON map of stable owner keys to unique secrets (URL-safe, 32-128 characters). Overrides `MCP_SECRET_SLUG`. |
| `MCP_SECRET_SLUG` | Legacy single link, using owner key `single`. |
| `FUNNEL_HOST` | Public hostname, no scheme, port, or path. Used for host and origin validation. |
| `PORT` | Local port, default `8000`. |
| `DATABASE_URL` | Backend PostgreSQL connection string. |
| `CHURNING_OWNER` | Required by the backend; use `public-unused`. Ownership is set per connection. |
| `OLLAMA_HOST`, `EMBED_MODEL` | Backend embedding service and the model matching the research index. |
| `MCP_PORTFOLIO_OWNERS` | Legacy, normally `[]`. Every link has portfolio access; listed keys must exist. |

The database role needs SELECT on research tables and `programs`; SELECT and INSERT
on `cards` plus USAGE on its ID sequence; and SELECT, INSERT, and UPDATE on
`point_balances`. Research tools use read-only connections.

Run the service from the directory containing `.env`. It binds to `127.0.0.1`; expose
it with Tailscale Funnel from a second terminal:

```bash
uv run --no-sync public-mcp
tailscale funnel --bg 8000
tailscale funnel status
```

See the [Tailscale Funnel docs](https://tailscale.com/docs/reference/tailscale-cli/funnel)
for setup. Each user's URL is `https://<FUNNEL_HOST>/<secret>/mcp`. There's no OAuth.
After server changes, restart and have users reconnect to refresh tools and prompts.

| Task | How |
| --- | --- |
| Rotate access | Replace the secret, restart, and send the new URL. Keep the owner key. |
| Revoke access | Remove the map entry and restart. Saved data is kept. |
| Stop Funnel | `tailscale funnel --https=443 off` |
| Test, lint, build | `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv build` |

## Access and data isolation

Each map key becomes the stored owner for that link's cards and balances. Ownership
is fixed server-side; no tool accepts an owner. The assistant is told never to use
keys or secrets as names.

A URL is a bearer credential: anyone with it can read and add that owner's cards and
balances. Keep owner keys stable when rotating, and never reassign one to another
person. Access logging is off; don't log secret URLs in proxies either.

Research tools come from an explicit `PUBLIC_TOOLS` allowlist, so new backend tools
are never exposed by accident. The backend's personal transaction and planning tools
are excluded.

## Contributing and CI

`main` is protected, including for admins: changes merge only through pull requests,
and the `build-and-test` check must pass on a branch up to date with `main`. Direct
pushes, force pushes, and deletion are blocked. No reviewer approval is required.

CI builds the wheel and sdist, installs the wheel, and runs the unit tests with the
backend and database mocked. It needs no secrets. Database permissions and tunnel
connectivity need separate checks after deployment.

```text
src/public_mcp/      # Package: HTTP service, tools, and starter prompts
tests/               # Unit tests with mocked backend
.github/workflows/   # CI
server.py            # Compatibility launcher (also: public-mcp, python -m public_mcp)
```

The `backend` extra installs the private sibling package; the public wheel and tests
don't need it. Keep the sibling checkout available when syncing with the lockfile.
Keep backend code, data, and deployment details in the private repository, and never
put secrets in issues or PRs.
