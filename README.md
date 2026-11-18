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
channel where you found this project. There's nothing to install: [Getting started](#getting-started)
takes about five minutes. Never post your link or card details in public issues.

## Getting started

Five steps, about five minutes. Nothing to install.

1. [Get your link](#1-get-your-link)
2. [Connect your app](#2-connect-your-app)
3. [Check it works](#3-check-it-works)
4. [Try a first command](#4-try-a-first-command)
5. [Add your cards (optional)](#5-add-your-cards-optional)

### 1. Get your link

Ask the maintainer for your private connection URL. It looks like
`https://<host>/<your-secret>/mcp`. The secret in the middle is your password: anyone
with the full URL can see and change your saved cards, so don't share or post it.

### 2. Connect your app

Paste the **whole URL** as a custom connector (some apps say "MCP server"). There's no
separate sign-in: choose **No authentication** / **None** if asked.

| App | Plan | Where to paste the URL |
| --- | --- | --- |
| **Claude** (easiest) | Free plan includes 1 custom connector | iOS app, web, or desktop: **Customize → Connectors → Add custom connector**, paste, **Next**, leave **No Sign In**. |
| Gemini | Free (US, 18+, **Keep Activity** on) | gemini.google.com: **Preferences → Skills → Connectors**, paste, accept. It then appears on iOS too. See [Gemini tip](#gemini-answers-from-my-email-instead). |
| ChatGPT / Codex | Plus, Team, or Enterprise | chatgpt.com: **Settings → Connectors / Developer Mode → Add custom MCP server**, paste, authentication **None**. Works on mobile after that. |
| Perplexity | Pro, Max, or Enterprise | Web or desktop: **Account Settings → Connectors → Add Connector**, paste. |
| Muse | Free with a Meta account | **Settings → Connectors**, or ask Muse in chat to build it ([message to send](#muse-setup-message)). Enter only the secret part of the URL on the credentials page. |
| Other MCP apps | Your own AI provider key | Apps such as ChatMCP or Joey MCP Client: add the URL as a Streamable HTTP server. |

This reflects November 2026; menus change, so check the app's help pages if a step
doesn't match.

### 3. Check it works

Make sure the **Churning** connector is switched on for the chat (most apps have a
toggle in the chat bar or tools menu), then send:

> **What can you do with the Churning connector?**

The assistant should describe card research, your portfolio and points tools. If it
answers from general knowledge or searches the web instead, see
[Troubleshooting](#troubleshooting).

### 4. Try a first command

Connecting doesn't send anything; you can ask research questions right away. Type one
of these, or pick it from the app's prompt menu if it shows one (many mobile apps don't;
typing works just as well):

| Type this | Prompt menu name | What happens |
| --- | --- | --- |
| Help me get started with card rewards research. | Get started | A short welcome, then a choice of what to do next. |
| Help me add my cards to my portfolio. | Set up my portfolio | Checks what's saved, then collects new cards. |
| Based on my portfolio, which card should I consider next? | Explore my next card | Combines your cards, goals, and current research. |
| Help me compare this points redemption with paying cash. | Evaluate a points redemption | Collects prices, points, and fees to compare. |

The assistant answers your question first and suggests adding a portfolio only when it
would help: at most once per conversation, and not after you decline.

### 5. Add your cards (optional)

Describe your cards in plain English. Ballpark answers are fine, and the assistant
looks up standard details (annual fee, business or personal, 5/24 reporting) itself
and asks only for what's missing:

> I have a Chase Sapphire Preferred I opened around March 2023 and an Amex Gold from
> last year. Walk me through what you need, save them, and show me what was saved.

Then say **Show me my saved portfolio** to check.

| Detail | Why it matters |
| --- | --- |
| Issuer and card name | Identifies what you already have. |
| Opening date | Timing rules such as Chase 5/24 depend on it. "Around March 2023" or "2023" works. |
| Annual fee | What each card costs to keep. Usually filled in for you. |
| Personal or business | Different rules apply. Usually filled in for you. |
| Reports to personal credit | Whether a card counts toward 5/24. Usually filled in for you. |

An approximate date is saved as the first of that month (January 1 for a year alone),
and the assistant tells you it's an estimate. Closer dates mean more accurate timing
advice. To change a saved card later (fee, notes, opening or closing date), just ask:
*"Update my Amex Gold: I closed it in June 2026."* Deleting a card entirely needs the
maintainer.

You can also save points totals: **Save my Chase Ultimate Rewards balance as 80,000
points.** A new amount replaces the old one. These are numbers you report, not a live
link to your bank.

Never share card numbers, security codes, passwords, or logins. The assistant never
needs them.

## What to ask

Cards and balances stay with your link across conversations. Goals, spending, and which
benefits you use aren't saved, so mention them when asked.

| Ask | What you get |
| --- | --- |
| Given my cards, what should I get next for a hotel trip? | Ideas that skip cards you hold and account for 5/24 and issuer rules. |
| Are my annual fees worth paying? | Starts from your saved fees and asks which benefits you use. |
| Am I eligible for the Bilt Palladium bonus? | Issuer rules checked against your history, with anything missing named. |
| Where should I transfer 100,000 Chase points? | Several airline and hotel options with ratios and caveats, not just one. |
| What's the best business class seat on Qatar's A350? | Seat product, layout, best seats, and a seat-map link. |
| Is a 2-3-2 business class worth booking? | How the layout rates (1-2-1 good, 2-3-2 poor) plus seat-picking tips. |
| What are people saying about Fluz and Taekus debit loops? | How loops work, risks, and the newest manufactured-spending reports. |
| What gets people shut down by Amex? | Do's and don'ts plus recent community reports, with dates. |
| What are people reporting about Amex retention offers? | Recent Reddit and blog data points, with links and dates. |

Answers cite dated sources. Offers and rules change, so confirm with the issuer before
applying. If the assistant's data looks out of date, say so and it will check the web
where the app allows it.

## Troubleshooting

#### The assistant doesn't use the connector

Check the Churning toggle is on for this chat, then name it in your message: *"Using my
Churning connector, what cards do I have?"* In ChatGPT and Gemini, typing `@Churning`
routes the question directly.

#### Gemini answers from my email instead

Gemini's Google Workspace extension (Gmail/Drive) can grab questions like *"check my
cards"* and mix in your emails. Tag `@Churning`, or turn off the Google Workspace
extension under **Settings → Extensions** if you don't need it.

#### New features don't show up

Apps cache the tool list. Remove and re-add the connector, or start a new chat, after
the maintainer announces an update.

#### Lost or leaked link

Ask the maintainer for a new one. Your saved cards and balances carry over; the old link
stops working.

#### Muse setup message

To have Muse build the connector, send this with your URL filled in:

> Build a custom connector for Churning using the remote MCP server at
> `<your connection URL>`. This URL is publicly hosted over the internet via Tailscale
> Funnel—connect directly over public HTTPS without requesting a Tailnet device invite.
> It uses Streamable HTTP transport and requires no separate API key or auth header
> because authentication is embedded in the URL path. Connect to the existing server
> without creating a local replacement, list the available tools, and save this
> connector for future chats.

When the credentials page asks, enter only the secret part of the URL.

## Tools

| Tool | Purpose |
| --- | --- |
| `get_portfolio` | Reads this link's cards. |
| `add_portfolio_card` | Saves a card the user supplies. A matching issuer, product, and opening date (case-insensitive) returns the existing card unchanged. Saves are serialized per owner and commit one card at a time. |
| `update_portfolio_card` | Updates fields (annual fee, notes, opening date estimate, closure date) on an existing card. |
| `get_point_balances` | Reads this link's points totals and their dates. |
| `set_point_balance` | Replaces one program's total; rejected if a newer-dated balance exists. |
| `list_point_programs` | Lists supported program codes. |
| `lookup_card_details` | Standard details, annual fees and fee history, business status, and 5/24 reporting for ~95 cards. |
| `search_card_offers`, `get_offer_history` | Tracked sign-up offers, historic highs, and recorded offer changes. |
| `evaluate_point_valuation`, `estimate_award_redemption_value`, `get_award_booking_window` | Transfer-partner values by airline and hotel, redemption value, and when awards open. |
| `search_data_points`, `get_document`, `get_document_context`, `get_search_coverage` | Dated Reddit, blog, and wiki evidence search. |
| `lookup_retention_playbook`, `lookup_reconsideration_guide`, `lookup_shutdown_risk` | Retention, reconsideration, and account-shutdown guidance with community data points. |
| `get_cabin_products` | Premium cabin seats by airline and aircraft, layout ratings, seat tips, and aeroLOPA seat-map links. |
| `simulate_manufactured_spend_fees`, `lookup_manufactured_spend` | Fee math, debit-loop mechanics and risks, and recent manufactured-spending reports. |

Starter prompts: `getting_started`, `build_portfolio`, `next_card`,
`evaluate_redemption`.

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

An unauthenticated health probe is available at `GET /health` (returning `{"status": "ok"}`)
for load balancers, container watchdogs, and tunnel monitoring without requiring a secret URL.

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

---

## How vector search and storage work

*(Implemented in the private `churning-mcp` backend repository)*

Credit card rewards research relies on unstructured community discussions (Reddit threads, comments, and blog articles) filled with shorthand, abbreviations, and informal phrasing (such as *"recon"*, *"pop-up jail / PUJ"*, *"HUCA"*, *"CSR AF hit"*, *"MDD"*, or *"retention offers"*). Standard keyword search fails when a user asks natural-language questions like *"How do I get approved after an initial denial?"* because the words do not literally match data points describing reconsideration calls or credit limit reallocations.

### Storage and indexing
- **Vector dimension:** Documents and queries are embedded into 768-dimensional representations using Ollama (`nomic-embed-text`).
- **`pgvector` + HNSW:** In PostgreSQL, embeddings are stored as `halfvec(768)` in the `documents` store and indexed using Hierarchical Navigable Small World (**HNSW**) graphs for fast cosine-distance (`<=>`) retrieval.
- **Hybrid retrieval (Vectors + Keywords):** Semantic vector search runs alongside PostgreSQL full-text search (GIN index with `ts_rank_cd`). Top candidates from both streams are merged using **Reciprocal Rank Fusion (RRF)**:
  $$\text{RRF Score} = \frac{1}{60 + \text{Rank}_{\text{semantic}}} + \frac{1}{60 + \text{Rank}_{\text{keyword}}}$$
  This ensures results capture conceptual intent while preserving exact matches for card names, bonus amounts, and alphanumeric terms.
- **Evidence grounding:** By fetching and reranking dated community evidence on demand, the assistant grounds answers in real data points rather than relying on stale or hallucinated model training data.

> [!NOTE]
> The full data ingestion pipeline, Arctic Shift sync, GPU-accelerated Ollama embedding workers, and `pgvector` database schema are hosted in the private `churning-mcp` backend repository.
