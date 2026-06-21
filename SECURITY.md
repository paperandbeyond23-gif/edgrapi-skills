# Security policy

## Reporting a vulnerability

Email **support@edgrapi.com** with the subject line `SECURITY: edgrapi-skills`. Please do not open public issues for security reports.

We will acknowledge receipt within 72 hours and aim to publish a fix or mitigation within 14 days for confirmed issues.

## Dependency surface

The handlers in this repository use only the Python standard library:

- `urllib.request`, `urllib.error`, `urllib.parse` — HTTPS calls to `edgrapi.com`
- `json` — response deserialization
- `os` — reading the `EDGRAPI_KEY` environment variable

There are no third-party packages, no transitive dependencies, and no build step. The only network destination is `https://edgrapi.com` — the base URL is **hardcoded**, so your `EDGRAPI_KEY` can never be transmitted to any other host.

## Credential handling

The skills read the API key from the `EDGRAPI_KEY` environment variable at call time. They do not cache the key, write it to disk, or log it. Failed requests return a structured error rather than raising, so the key cannot leak into a traceback.

## Independence

Edgrapi is an independent service and is not affiliated with, endorsed by, or sponsored by the U.S. Securities and Exchange Commission. All data originates from the SEC's public EDGAR system.
