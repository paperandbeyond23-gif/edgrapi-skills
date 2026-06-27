# edgrapi-skills

**Agent skills for clean company financials from SEC EDGAR.** Drop-in skills that let any agent pull normalized income/balance/cash-flow fundamentals, computed ratios, company profiles, and recent SEC filings for any US-listed ticker — over the [Edgrapi REST API](https://edgrapi.com).

EDGAR is free, but its XBRL company-facts payloads are brutal to parse (tag drift, mixed periods, trailing-twelve-month windows hiding inside 10-Qs). Edgrapi normalizes all of that into clean JSON, keyed by fiscal period — so your agent gets numbers it can trust in one call.

Free to start — [grab a key](https://edgrapi.com/app) (100 free credits, no card required) and you're pulling fundamentals from Claude, ChatGPT, Cursor, or your own agent loop in under two minutes.

Pure Python standard library. No dependencies. MIT-0 licensed.

## Install

```bash
# Claude Code, Cursor, Cline, etc. — `skills` CLI, installs straight from this repo
npx skills add paperandbeyond23-gif/edgrapi-skills --all
# or pick one: npx skills add paperandbeyond23-gif/edgrapi-skills --skill edgrapi-full

# OpenClaw / ClawHub — published to the ClawHub registry
npx clawhub@latest install edgrapi-full   # also: edgrapi-fundamentals, edgrapi-filings
```

## Skills in this repo

| Skill | Purpose |
|---|---|
| [`edgrapi-full`](skills/edgrapi-full) | Complete toolkit — fundamentals, ratios, company profile, and filings |
| [`edgrapi-fundamentals`](skills/edgrapi-fundamentals) | Normalized financial statements + computed ratios |
| [`edgrapi-filings`](skills/edgrapi-filings) | Company profiles + recent SEC filings (10-K/10-Q/8-K) |

Install the bundled `edgrapi-full` for agents that need broad coverage. Install the focused variants when you want minimum tool surface.

## Tools

| Tool | Returns |
|---|---|
| `get_fundamentals(ticker, period, limit)` | Income statement, balance sheet, cash flow — periodized, USD |
| `get_ratios(ticker)` | Margins, returns (ROE/ROA), leverage, liquidity |
| `get_company(ticker)` | CIK, legal name, SIC industry, fiscal-year end, exchanges, website |
| `get_filings(ticker, limit, form)` | Recent filings with filing/report dates and document links |

## Authentication

Set the `EDGRAPI_KEY` environment variable to your Edgrapi key (format `edgr_...`). It's sent as the `X-API-Key` header — the base URL is hardcoded, so the key never reaches any other host.

```bash
export EDGRAPI_KEY="edgr_..."
```

**[Get a free key](https://edgrapi.com/app)** — 100 free credits, no card required. The same key works for these skills and direct REST calls.

## Pricing

1 credit = 1 request. Credits never expire. All data is from public SEC EDGAR.

| Plan | Price | Credits |
|---|---|---|
| Free | $0 | 100 one-time |
| Pro (monthly) | $29/mo | 60,000 / mo |
| Pro (annual) | $290/yr | 720,000 up front |

Top-up packs (one-time, never expire): 10,000 / $7 · 30,000 / $18 · 100,000 / $55.

Manage plans at <https://edgrapi.com/pricing>. Also available metered on RapidAPI.

## Source

- Docs: <https://edgrapi.com/docs> · OpenAPI: <https://edgrapi.com/openapi.json>
- Quickstart: get a key at <https://edgrapi.com/app>, then call any tool

## Issues and contributions

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).

## License

[MIT No Attribution](LICENSE). Fork, ship, sublicense — no attribution required.

## Independence

Edgrapi is an independent service and is not affiliated with, endorsed by, or sponsored by the U.S. Securities and Exchange Commission. All data originates from the SEC's public EDGAR system. "EDGAR" is a system operated by the U.S. SEC.
