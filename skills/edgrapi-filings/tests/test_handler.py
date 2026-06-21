"""Smoke tests for the edgrapi-filings handler. No network — urlopen is mocked."""

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
            result = handler.get_company(ticker="AAPL")
        self.assertEqual(result["error"], "auth_required")
        self.assertIn("EDGRAPI_KEY", result["detail"])


class TestInputValidation(unittest.TestCase):
    def test_company_requires_ticker(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(handler.get_company(ticker="")["error"], "invalid_argument")

    def test_filings_requires_ticker(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(handler.get_filings(ticker="")["error"], "invalid_argument")


class TestEndpoints(unittest.TestCase):
    @patch("handler.urllib.request.urlopen")
    def test_company_gets_v1_company(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_company(ticker="nvda")
        self.assertEqual(_req(mock_urlopen).full_url, "https://edgrapi.com/v1/company/NVDA")

    @patch("handler.urllib.request.urlopen")
    def test_filings_filters_by_form(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_filings(ticker="TSLA", limit=5, form="8-K")
        url = _req(mock_urlopen).full_url
        self.assertIn("https://edgrapi.com/v1/filings/TSLA", url)
        self.assertIn("form=8-K", url)
        self.assertIn("limit=5", url)
        self.assertEqual(_req(mock_urlopen).headers["X-api-key"], "edgr_test")

    @patch("handler.urllib.request.urlopen")
    def test_filings_omits_unset_form(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"{}")
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            handler.get_filings(ticker="AAPL")
        self.assertNotIn("form=", _req(mock_urlopen).full_url)


class TestHttpErrors(unittest.TestCase):
    @patch("handler.urllib.request.urlopen")
    def test_404_maps_to_ticker_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://edgrapi.com/v1/company/ZZZZ", 404, "Not Found", None, None
        )
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            self.assertEqual(handler.get_company(ticker="ZZZZ")["error"], "ticker_not_found")


if __name__ == "__main__":
    unittest.main()
