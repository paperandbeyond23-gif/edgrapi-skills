"""Post SEC cluster-buy alerts to Slack.

A cluster buy is several company insiders buying their own stock on the open market
within a short window. It's a stronger signal than one insider buying alone, because
a lone purchase can be routine and three at once usually isn't.

Run it on a schedule (cron, GitHub Actions, a Lambda). It remembers what it already
posted, so you get each cluster once rather than every run.

    export EDGRAPI_KEY=edgr_...          # free key: https://edgrapi.com/app
    export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
    python alert.py
"""

import json, os, pathlib, urllib.request

API = "https://api.edgrapi.com/v1/insider/clusters"
SEEN = pathlib.Path(__file__).with_name(".seen.json")

# 3+ insiders buying inside 15 days, $50k+ combined. Loosen days or drop min_insiders
# to 2 if you want more signal and more noise.
PARAMS = "?days=15&min_insiders=3&min_value=50000&limit=20"


def get(url, headers=None, data=None):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    key = os.environ["EDGRAPI_KEY"]
    hook = os.environ["SLACK_WEBHOOK_URL"]

    body = get(API + PARAMS, {"X-API-Key": key})
    clusters = json.loads(body)["clusters"]

    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    fresh = [c for c in clusters if c["ticker"] not in seen]

    for c in fresh:
        # buyers[] is already deduped per person and sorted by size
        who = ", ".join(
            "%s (%s)" % (b["owner"], b["officer_title"] or "insider") for b in c["buyers"][:4]
        )
        text = "*%s*: %d insiders bought $%s\n%s\n%s" % (
            c["ticker"],
            c["insider_count"],
            "{:,.0f}".format(c["total_value"]),
            who,
            c["buyers"][0]["filed_url"] or "",
        )
        get(hook, {"Content-Type": "application/json"}, json.dumps({"text": text}).encode())
        print("posted", c["ticker"])

    SEEN.write_text(json.dumps(sorted(seen | {c["ticker"] for c in clusters})))
    print("%d clusters, %d new" % (len(clusters), len(fresh)))


if __name__ == "__main__":
    main()
