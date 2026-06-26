"""
edgrapi-fundamentals skill handler — normalized financial statements and computed
ratios from SEC EDGAR over the Edgrapi REST API: get_fundamentals, get_ratios.

Pure standard library. API key in EDGRAPI_KEY, sent as the X-API-Key header.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://edgrapi.com"  # hardcoded: the API key is never sent to any other host
USER_AGENT = "edgrapi-skills/1.0.0 (+https://github.com/paperandbeyond23-gif/edgrapi-skills)"
TIMEOUT_SECONDS = 60

SIGNUP_URL = "https://edgrapi.com/app"
KEYS_URL = "https://edgrapi.com/app"
PRICING_URL = "https://edgrapi.com/pricing"

PERIODS = ("annual", "quarterly")


def _key():
    k = os.environ.get("EDGRAPI_KEY", "").strip()
    if not k:
        raise RuntimeError(
            "EDGRAPI_KEY environment variable is not set. "
            "Get a free key (100 free credits, no card) at " + SIGNUP_URL + ", "
            "then export EDGRAPI_KEY=edgr_..."
        )
    return k


def _http_error(e):
    try:
        detail = e.read().decode("utf-8")[:1000]
    except Exception:
        detail = ""
    if e.code == 401:
        return {"error": "auth_invalid",
                "detail": "EDGRAPI_KEY was rejected. Mint a new key at " + KEYS_URL + ".",
                "keys_url": KEYS_URL, "http_status": 401}
    if e.code == 403:
        return {"error": "rapidapi_only",
                "detail": "This Edgrapi origin is locked to RapidAPI subscribers.",
                "http_status": 403}
    if e.code == 404:
        return {"error": "ticker_not_found",
                "detail": "No SEC filer matches that ticker. Use the exact listed symbol.",
                "http_status": 404}
    if e.code == 402:
        return {"error": "out_of_credits",
                "detail": "Out of Edgrapi credits. Top up a pack or subscribe at " + PRICING_URL + ".",
                "upgrade_url": PRICING_URL, "http_status": 402}
    if e.code == 429:
        return {"error": "rate_limit_exceeded",
                "detail": "Plan request limit hit. Back off, or upgrade at " + PRICING_URL + ".",
                "upgrade_url": PRICING_URL, "http_status": 429}
    if e.code == 502:
        return {"error": "edgar_unavailable",
                "detail": "SEC EDGAR was unreachable upstream. Retry shortly.",
                "http_status": 502}
    return {"error": "HTTP " + str(e.code), "detail": detail}


def _get(path, params=None):
    try:
        qs = ""
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                qs = "?" + urllib.parse.urlencode(clean)
        req = urllib.request.Request(
            API_BASE + path + qs, method="GET",
            headers={"X-API-Key": _key(), "User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return _http_error(e)
    except urllib.error.URLError as e:
        return {"error": "network", "detail": str(e.reason)}
    except RuntimeError as e:
        return {"error": "auth_required", "detail": str(e), "signup_url": SIGNUP_URL}
    except Exception as e:
        return {"error": "unexpected", "detail": str(e)}


def _ticker(t):
    return urllib.parse.quote((t or "").strip().upper(), safe="")


def get_fundamentals(ticker, period="annual", limit=5):
    """
    Normalized income-statement, balance-sheet, and cash-flow figures for `ticker`,
    parsed from SEC EDGAR XBRL companyfacts.

    period: "annual" (10-K) or "quarterly" (10-Q), default "annual".
    limit:  number of periods to return, 1-20 (default 5).
    """
    if not ticker:
        return {"error": "invalid_argument", "detail": "ticker is required."}
    if period not in PERIODS:
        return {"error": "invalid_argument", "detail": "period must be 'annual' or 'quarterly'."}
    return _get("/v1/fundamentals/" + _ticker(ticker), {"period": period, "limit": limit})


def get_ratios(ticker):
    """
    Computed financial ratios for `ticker` (margins, returns, leverage, liquidity)
    derived from SEC EDGAR fundamentals. Price-based ratios (P/E, P/B) are not
    included — EDGAR carries no market price.
    """
    if not ticker:
        return {"error": "invalid_argument", "detail": "ticker is required."}
    return _get("/v1/ratios/" + _ticker(ticker))
