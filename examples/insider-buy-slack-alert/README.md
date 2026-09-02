# Insider-buy Slack alert

Posts a Slack message when several insiders at the same company buy their own stock inside a short
window. About 40 lines, no dependencies beyond the standard library.

A single insider buying can be routine. Three of them buying in the same fortnight usually isn't,
which is why the cluster is the thing worth alerting on rather than every Form 4.

## Run it

```bash
export EDGRAPI_KEY=edgr_...          # free key, no card: https://edgrapi.com/app
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
python alert.py
```

Put it on a schedule, once or twice a day is plenty since Form 4s land within two business days of
the trade. It writes a `.seen.json` beside itself so each cluster is posted once instead of on
every run.

## What comes out

```
*ACME*: 3 insiders bought $412,500
Jane Roe (CFO), John Doe (insider), A Third (COO)
https://www.sec.gov/Archives/edgar/data/...
```

## Tuning

`PARAMS` at the top of the script:

| Parameter | Default | What it does |
|---|---|---|
| `days` | 15 | Lookback window |
| `min_insiders` | 3 | Distinct people who must have bought |
| `min_value` | 50000 | Minimum combined USD across the cluster |
| `limit` | 20 | Max clusters returned |

Dropping `min_insiders` to 2 gives you a lot more hits, most of which won't mean much, since two
people buying in the same window happens for ordinary reasons. Widening `days` too far runs into the
fact that a 13F-style lag isn't the issue here, Form 4s land within two business days, so a long
window mostly just re-surfaces trades you already saw.

## Worth knowing

Only open-market purchases count here, transaction code P, and that distinction is doing most of the
work. Option exercises and vesting show up on Form 4 as acquisitions too, but an insider receiving
shares as compensation tells you nothing, whereas one spending their own money is a decision. Sales are
excluded for the same reason, and most are pre-scheduled 10b5-1 anyway.

The endpoint costs 5 credits per call. On the free tier that's 20 calls a month, so once a day needs
a paid plan; twice a week doesn't.

Cluster buying has historically preceded higher abnormal returns than a lone insider purchase. That
is a statistical tendency across many companies, not a prediction about any one of them, and none of
this is investment advice.

## The call behind it

```bash
curl "https://api.edgrapi.com/v1/insider/clusters?days=15&min_insiders=3" \
  -H "X-API-Key: edgr_..."
```

Same data as the script, if you'd rather wire it somewhere other than Slack. Full API at
[edgrapi.com/docs](https://edgrapi.com/docs); there's also an MCP server at
`https://api.edgrapi.com/mcp` if you want your agent to ask for this directly.
