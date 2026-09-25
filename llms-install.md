# Installing the Edgrapi MCP server

Instructions for an AI agent (Cline, Claude, Cursor, Windsurf) setting this server up.

Edgrapi is a **hosted, remote** MCP server. There is nothing to clone, build or run. Pick one of
the two routes below; the first is simpler and is what you should prefer.

## Route 1 (preferred): connect to the URL

Add the remote server and let the client run OAuth in the browser. There is no key to paste and no
secret in a config file.

```
https://api.edgrapi.com/mcp
```

The server is its own OAuth 2.1 authorization server and supports dynamic client registration and
PKCE, so the URL alone is enough. For clients that take a remote server in `mcp.json`:

```json
{
  "mcpServers": {
    "edgrapi": {
      "url": "https://api.edgrapi.com/mcp"
    }
  }
}
```

If the client cannot do OAuth, send the key as a bearer token instead:

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

## Route 2: stdio, for clients that only speak stdio

A dependency-free bridge forwards stdio to the same hosted endpoint. It needs an API key, because a
browser sign-in inside a piped process is a bad experience.

Use Docker (`-i` matters: stdio clients need stdin held open):

```json
{
  "mcpServers": {
    "edgrapi": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "EDGRAPI_API_KEY", "ghcr.io/paperandbeyond23-gif/edgrapi-mcp"],
      "env": { "EDGRAPI_API_KEY": "edgr_YOUR_KEY" }
    }
  }
}
```

## Getting a key

Only needed for Route 2, or for Route 1 without OAuth. Free tier is 100 credits a month with no
card: https://edgrapi.com/app — keys look like `edgr_...`.

## Verifying the install

`tools/list` needs no credential, so this confirms reachability on its own:

```bash
curl -s -X POST https://api.edgrapi.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Expect 19 tools. The same check through the Docker bridge:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | docker run -i --rm ghcr.io/paperandbeyond23-gif/edgrapi-mcp
```

A `tools/call` without a valid credential returns a JSON-RPC error saying authentication is
required. That is the expected response, not a broken install.

## What you get

19 tools, all read-only:

- `get_opportunities` — SAM.gov federal contract opportunities
- `get_awards` — USAspending awards and spending
- `get_grants` — Grants.gov grant opportunities
- `get_congress` — House STOCK Act congressional stock trades
- SEC EDGAR: `get_insider`, `get_events`, `get_holdings`, `get_activist`, `get_fundamentals`,
  `get_ratios`, `get_company`, `get_filings`, `get_sections`, `get_xbrl`, `get_shares`,
  `get_form_d`, `get_subsidiaries`, `resolve_entity`, `search_filings`

Calls cost 1–5 credits by weight. Every record links back to the official source. Data is only as
fresh as each agency publishes it; congressional trades run up to 45 days behind by law, report
dollar ranges rather than exact amounts, and cover the House only for now.

## Troubleshooting

- **401 / "Authentication required"** — expected for `tools/call` without a credential. Finish the
  OAuth flow, or set `EDGRAPI_API_KEY`.
- **"Invalid API key"** — the key reached the server but is wrong. Mint a new one at
  https://edgrapi.com/app.
- **"Out of credits"** — the free tier renews monthly.
- **Docker exits immediately** — `-i` is missing. Without it stdin closes and the bridge shuts down.
