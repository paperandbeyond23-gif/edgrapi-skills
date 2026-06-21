"""Smoke tests for the edgrapi-full handler. No network — urlopen is mocked."""

import os
import sys
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import handler  # noqa: E402


def _mock_response(body):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = body
    return cm


def _req(mock_urlopen):
    return mock_urlopen.call_args[0][0]


class TestAuth(unittest.TestCase):
    def test_missing_key_returns_auth_required(self):
        with patch.dict(os.environ, {}, clear=True):
            result = handler.get_fundamentals(ticker="AAPL")
        self.assertEqual(result["error"], "auth_required")
        self.assertIn("EDGRAPI_KEY", result["detail"])
        self.assertEqual(result["signup_url"], "https://edgrapi.com/app")


class TestInputValidation(unittest.TestCase):
    def test_fundamentals_requires_ticker(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(handler.get_fundamentals(ticker="")["error"], "invalid_argument")

    def test_fundamentals_rejects_bad_period(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(
                handler.get_fundamentals(ticker="AAPL", period="ttm")["error"], "invalid_argument"
            )

    def test_ratios_requires_ticker(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(handler.get_ratios(ticker="")["error"], "invalid_argument")


class TestEndpoints(unittest.TestCase):
    @patch("handler.urllib.request.urlopen")
    def test_fundamentals_gets_v1_fundamentals(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_fundamentals(ticker="aapl", period="quarterly", limit=8)
        url = _req(mock_urlopen).full_url
        self.assertIn("https://edgrapi.com/v1/fundamentals/AAPL", url)
        self.assertIn("period=quarterly", url)
        self.assertIn("limit=8", url)

    @patch("handler.urllib.request.urlopen")
    def test_ratios_gets_v1_ratios(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_ratios(ticker="MSFT")
        self.assertEqual(_req(mock_urlopen).full_url, "https://edgrapi.com/v1/ratios/MSFT")

    @patch("handler.urllib.request.urlopen")
    def test_company_gets_v1_company(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_company(ticker="NVDA")
        self.assertEqual(_req(mock_urlopen).full_url, "https://edgrapi.com/v1/company/NVDA")

    @patch("handler.urllib.request.urlopen")
    def test_filings_filters_by_form(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_filings(ticker="TSLA", limit=5, form="10-K")
        url = _req(mock_urlopen).full_url
        self.assertIn("https://edgrapi.com/v1/filings/TSLA", url)
        self.assertIn("form=10-K", url)
        self.assertIn("limit=5", url)

    @patch("handler.urllib.request.urlopen")
    def test_api_key_header_is_set(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_secret"}):
            handler.get_company(ticker="AAPL")
        req = _req(mock_urlopen)
        self.assertEqual(req.headers["X-api-key"], "edgr_secret")
        self.assertIn("edgrapi-skills", req.headers["User-agent"])


class TestHttpErrors(unittest.TestCase):
    @patch("handler.urllib.request.urlopen")
    def test_404_maps_to_ticker_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://edgrapi.com/v1/company/ZZZZ", 404, "Not Found", None, None
        )
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            result = handler.get_company(ticker="ZZZZ")
        self.assertEqual(result["error"], "ticker_not_found")

    @patch("handler.urllib.request.urlopen")
    def test_429_maps_to_rate_limit(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://edgrapi.com/v1/ratios/AAPL", 429, "Too Many Requests", None, None
        )
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            result = handler.get_ratios(ticker="AAPL")
        self.assertEqual(result["error"], "rate_limit_exceeded")
        self.assertEqual(result["upgrade_url"], "https://edgrapi.com/pricing")

    @patch("handler.urllib.request.urlopen")
    def test_401_maps_to_auth_invalid(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://edgrapi.com/v1/ratios/AAPL", 401, "Unauthorized", None, None
        )
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_bad"}):
            result = handler.get_ratios(ticker="AAPL")
        self.assertEqual(result["error"], "auth_invalid")


if __name__ == "__main__":
    unittest.main()
