# edgrapi-skills

**US government data for AI agents — five official sources, one key, one JSON schema.**

SAM.gov contract opportunities, USAspending awards, Grants.gov funding, US House STOCK Act trades,
and SEC EDGAR filings, served as a hosted MCP server plus drop-in Python skills, over the
[Edgrapi API](https://edgrapi.com).

Every one of those sources is free and public. Each also ships its own headache: SAM.gov takes
`ncode` where you'd expect `naics` and silently ignores unknown filters, its dates are MM/dd/yyyy
and its query window caps at a year; USAspending's `hasNext` goes false at record 10,000 while real
rows continue to 50,000; EDGAR gives you XBRL tag drift. Edgrapi normalises all of it into one
schema so your agent gets numbers it can trust in one call.

Free to start — [grab a key](https://edgrapi.com/app), 100 credits every month, no card.

Pure Python standard library. No dependencies. MIT-0 licensed.

## Fastest path: the hosted MCP server

Nothing to install, no local process. Point any MCP client at one URL:

```json
{
  "mcpServers": {
    "edgrapi": {
      "url": "https://api.edgrapi.com/mcp",
      "headers": { "Authorization": "Bearer edgr_YOUR_KEY" }
    }
  }
}
```

Works in Claude Desktop, Claude Code, Cursor and Cline. Transport is streamable-http. Auth is a
bearer `edgr_` key or OAuth 2.1 with PKCE — the server is its own provider and supports dynamic
client registration. Discovery (`initialize`, `tools/list`) is open, so you can inspect the full
tool list before you have a key; `tools/call` needs one.

## Other ways in

```bash
# Python client
pip install edgrapi

# Docker — the MCP server as a container
docker run -e EDGRAPI_API_KEY=edgr_... ghcr.io/paperandbeyond23-gif/edgrapi-mcp:latest

# Python skills from this repo, via the skills CLI
npx skills add paperandbeyond23-gif/edgrapi-skills --all
npx skills add paperandbeyond23-gif/edgrapi-skills --skill edgrapi-full
```

Also listed in the [Official MCP Registry](https://registry.modelcontextprotocol.io) as
`io.github.paperandbeyond23-gif/edgrapi-skills`.

## What the MCP server covers

19 tools, all read-only.

| Source | Tools | Credits |
|---|---|---|
| **SAM.gov** | `get_opportunities` — contract opportunities by NAICS, set-aside, state, type | 2 |
| **USAspending** | `get_awards` — contracts, grants, loans, direct payments | 2 |
| **Grants.gov** | `get_grants` — funding opportunities with CFDA numbers and deadlines | 2 |
| **Congress** | `get_congress` — US House STOCK Act stock trades | 2 |
| **SEC EDGAR** | `get_insider` (Form 4, with cluster-buy detection), `get_holdings` (13F, diffed quarter-over-quarter), `get_activist` (13D/G >5% stakes), `get_events` (typed 8-K), `get_fundamentals`, `get_ratios`, `get_sections`, `get_company`, `get_filings`, XBRL-to-JSON, entity resolution, full-text search | 1–5 |

For the live list, call `tools/list` or read the
[server card](https://api.edgrapi.com/.well-known/mcp/server-card.json) — both are generated from
the server, so neither goes stale.

## Skills in this repo

The packaged Python skills cover the SEC company-financials workflow. Use the MCP server for the
government-data tools.

| Skill | Purpose |
|---|---|
| [`edgrapi-full`](skills/edgrapi-full) | Fundamentals, ratios, company profile and filings |
| [`edgrapi-fundamentals`](skills/edgrapi-fundamentals) | Normalised financial statements + computed ratios |
| [`edgrapi-filings`](skills/edgrapi-filings) | Company profiles + recent 10-K/10-Q/8-K |

## Authentication

Set `EDGRAPI_KEY` to your key (format `edgr_...`). It is sent as the `X-API-Key` header, and the
base URL is hardcoded, so the key never reaches any other host.

```bash
export EDGRAPI_KEY="edgr_..."
```

**[Get a free key](https://edgrapi.com/app)** — 100 credits every month, no card. The same key works
for the skills, the MCP server and direct REST.

## Pricing

Credits are weighted by endpoint, not one per request. Government endpoints cost 2. On the SEC side,
company, filings, events, entity resolution and full-text search cost 1; fundamentals, ratios and
XBRL cost 3; sections, insider, holdings and activist cost 5. The exact cost of a call comes back in
the `X-Credits-Cost` header.

| Plan | Price | Credits |
|---|---|---|
| Free | $0 | 100 / month, renewing |
| Starter | $10/mo | 10,000 / month |
| Pro | $29/mo | 30,000 / month |
| Pro annual | $290/yr | 360,000 up front |
| Business | $99/mo | 150,000 / month |

Top-up packs, one-time and never expiring: 5,000 / $7 · 15,000 / $18 · 50,000 / $55. Paid-plan
credits roll over. Full details at <https://edgrapi.com/pricing>. Also available metered on RapidAPI.

## Limits, stated plainly

- **Congressional trades are US House only**, reported as dollar ranges, and lag up to 45 days by law.
- **No state or local (SLED) procurement.** Federal only.
- **Contract alerts poll daily**, not in realtime, so a notice can be up to a day old when it lands.
- **Freshness is each source's own cadence.** Edgrapi normalises the official feeds; it does not
  hold or restate anything.
- USAspending search cannot reach before 2007-10-01, and EDGAR full-text search covers 2001 onward.

## Source

- Docs: <https://edgrapi.com/docs> · OpenAPI 3.1: <https://edgrapi.com/openapi.json>
- Agent guide: <https://edgrapi.com/agents> · Status: <https://edgrapi.com/status>

## Issues and contributions

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).

## License

[MIT No Attribution](LICENSE). Fork, ship, sublicense — no attribution required.

## Independence

Edgrapi is an independent service, not affiliated with, endorsed by or sponsored by the U.S.
Securities and Exchange Commission, the General Services Administration, SAM.gov, USAspending.gov,
Grants.gov, or the U.S. House of Representatives. All data originates from those bodies' public
systems and is in the public domain.
