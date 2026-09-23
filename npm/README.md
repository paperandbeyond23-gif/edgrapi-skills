# Edgrapi MCP — US government data for your AI agent

[![npm](https://img.shields.io/npm/v/edgrapi-mcp?color=1C6E5A)](https://www.npmjs.com/package/edgrapi-mcp)
[![Website](https://img.shields.io/badge/site-edgrapi.com-1C6E5A)](https://edgrapi.com)
[![MCP](https://img.shields.io/badge/MCP-streamable--http-6E56CF)](https://api.edgrapi.com/mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Federal contract opportunities, awards, grants, congressional trades and SEC filings as clean
JSON, in one call.**

[Edgrapi](https://edgrapi.com) is a hosted [Model Context Protocol](https://modelcontextprotocol.io)
server (and a plain REST API) for US government data:

- **SAM.gov** federal contract opportunities
- **USAspending** awards and spending
- **Grants.gov** grant opportunities
- **House STOCK Act** congressional stock trades
- **SEC EDGAR** insider trades, 8-K events, 13F holdings, 13D/G stakes, fundamentals, ratios,
  XBRL-to-JSON, filings, 10-K/10-Q sections and full-text search

19 tools, all read-only. Every record links back to the official source.

The data is free at the source. Getting it out is the work: SAM.gov keys take a while and then cap
your day, USAspending wants a request body you have to learn, Grants.gov has its own conventions,
and every source returns a different shape. Edgrapi normalizes them.

## The fastest route: point your client at the URL

Edgrapi is a **remote** MCP server, so most clients need no install at all. Add the URL and sign in
with OAuth (the server is its own OAuth 2.1 provider, with dynamic client registration and PKCE):

```
https://api.edgrapi.com/mcp
```

In Claude: Settings → Connectors → Add custom connector. In Cursor, Windsurf or Cline: add it as a
remote server in `mcp.json`. There is no key to paste and no secret in a config file.

## This package: a stdio bridge

Some clients only speak stdio, and some registries want an install command. That is what this
package is: a small bridge that reads MCP messages on stdin, forwards them to the hosted endpoint,
and writes the reply back. It has **no dependencies** and holds no state. The hosted server is
still the only thing serving tools and data.

```bash
npx -y edgrapi-mcp
```

```jsonc
{
  "mcpServers": {
    "edgrapi": {
      "command": "npx",
      "args": ["-y", "edgrapi-mcp"],
      "env": { "EDGRAPI_API_KEY": "edgr_your_key_here" }
    }
  }
}
```

Docker works the same way. `-i` matters, because stdio clients need stdin to stay open:

```bash
docker run -i --rm -e EDGRAPI_API_KEY=edgr_... ghcr.io/paperandbeyond23-gif/edgrapi-mcp
```

```jsonc
{
  "mcpServers": {
    "edgrapi": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "EDGRAPI_API_KEY", "ghcr.io/paperandbeyond23-gif/edgrapi-mcp"],
      "env": { "EDGRAPI_API_KEY": "edgr_your_key_here" }
    }
  }
}
```

### Options

| Flag | Environment variable | Default |
| --- | --- | --- |
| `--key`, `-k` | `EDGRAPI_API_KEY` | none (requests go out unauthenticated and the server answers 401) |
| `--url`, `-u` | `EDGRAPI_MCP_URL` | `https://api.edgrapi.com/mcp` |

The bridge uses an API key rather than OAuth on purpose: a browser sign-in flow inside a piped
stdio process is a bad experience. If you want OAuth, use the URL directly as shown above.

## Auth and pricing

- **Key:** `Authorization: Bearer edgr_<key>`, or OAuth 2.1 when you connect by URL
- **Free tier:** 100 credits a month, no card — [get a key](https://edgrapi.com/app)
- Calls cost 1–5 credits depending on weight

## Tools

The live list comes from the server, so it cannot go stale here:

```bash
curl -s -X POST https://api.edgrapi.com/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Also in the [server card](https://api.edgrapi.com/.well-known/mcp/server-card.json).

## Freshness and limits

Data is as fresh as each source publishes it. Congressional trades run up to 45 days behind by law,
report dollar ranges rather than exact amounts, and cover the House only for now.

## Registry listing

The canonical [MCP registry](https://registry.modelcontextprotocol.io) entry is
`io.github.paperandbeyond23-gif/edgrapi-skills`, published from
[this repo's `server.json`](../server.json). The Python agent skills for the SEC
company-financials workflow live in [`../skills`](../skills).

## Development

```bash
cd npm && node test/smoke.js   # speaks MCP to the bridge against the live server
```

Set `EDGRAPI_API_KEY` first and the smoke test also makes a real tool call.

## License

MIT
