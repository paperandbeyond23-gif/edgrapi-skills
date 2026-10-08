"""Smoke tests for the edgrapi-gov handler. No network — urlopen is mocked."""

import json
import os
import sys
import unittest
import urllib.error
import urllib.parse
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import handler  # noqa: E402


def _mock_response(body):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = body
    return cm


def _req(mock_urlopen):
    return mock_urlopen.call_args[0][0]


def _qs(mock_urlopen):
    return urllib.parse.parse_qs(urllib.parse.urlparse(_req(mock_urlopen).full_url).query)


class TestAuth(unittest.TestCase):
    def test_missing_key_returns_auth_required(self):
        with patch.dict(os.environ, {}, clear=True):
            result = handler.get_opportunities()
        self.assertEqual(result["error"], "auth_required")
        self.assertIn("EDGRAPI_KEY", result["detail"])
        self.assertEqual(result["signup_url"], "https://edgrapi.com/app")

    def test_key_is_sent_as_x_api_key(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
                handler.get_grants()
        self.assertEqual(_req(m).get_header("X-api-key"), "edgr_test")

    def test_key_never_leaves_the_edgrapi_host(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
                handler.get_awards(recipient="Lockheed")
        self.assertTrue(_req(m).full_url.startswith("https://edgrapi.com/"))


class TestRouting(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_opportunities_path(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_opportunities(naics="541511", set_aside="SBA")
        self.assertIn("/v1/opportunities", _req(m).full_url)
        q = _qs(m)
        self.assertEqual(q["naics"], ["541511"])
        self.assertEqual(q["set_aside"], ["SBA"])

    def test_awards_path_and_defaults(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_awards()
        self.assertIn("/v1/awards", _req(m).full_url)
        q = _qs(m)
        self.assertEqual(q["category"], ["contracts"])
        self.assertEqual(q["sort"], ["amount"])
        self.assertEqual(q["order"], ["desc"])

    def test_grants_path(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_grants(aln="93.217")
        self.assertIn("/v1/grants", _req(m).full_url)
        self.assertEqual(_qs(m)["aln"], ["93.217"])

    def test_congress_path(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_congress(action="buy")
        self.assertIn("/v1/congress", _req(m).full_url)
        self.assertEqual(_qs(m)["action"], ["buy"])

    def test_congress_ticker_is_uppercased_and_escaped(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_congress_ticker(" nvda ")
        self.assertIn("/v1/congress/NVDA", _req(m).full_url)

    def test_none_params_are_dropped(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"{}")) as m:
            handler.get_opportunities(naics=None, state="TX")
        q = _qs(m)
        self.assertNotIn("naics", q)
        self.assertEqual(q["state"], ["TX"])


class TestInputValidation(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_bad_ptype_rejected_without_network(self):
        with patch("urllib.request.urlopen") as m:
            result = handler.get_opportunities(ptype="x")
        self.assertEqual(result["error"], "invalid_argument")
        m.assert_not_called()

    def test_bad_award_category_rejected(self):
        self.assertEqual(handler.get_awards(category="widgets")["error"], "invalid_argument")

    def test_bad_order_rejected(self):
        self.assertEqual(handler.get_awards(order="sideways")["error"], "invalid_argument")

    def test_bad_congress_action_rejected(self):
        self.assertEqual(handler.get_congress(action="hold")["error"], "invalid_argument")

    def test_congress_ticker_required(self):
        self.assertEqual(handler.get_congress_ticker("")["error"], "invalid_argument")


class TestErrorMapping(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _raise(self, code):
        return urllib.error.HTTPError("https://edgrapi.com/v1/grants", code, "e", {}, None)

    def test_401_maps_to_auth_invalid(self):
        with patch("urllib.request.urlopen", side_effect=self._raise(401)):
            self.assertEqual(handler.get_grants()["error"], "auth_invalid")

    def test_402_maps_to_out_of_credits_with_upgrade_url(self):
        with patch("urllib.request.urlopen", side_effect=self._raise(402)):
            r = handler.get_grants()
        self.assertEqual(r["error"], "out_of_credits")
        self.assertEqual(r["upgrade_url"], "https://edgrapi.com/pricing")

    def test_429_maps_to_rate_limit(self):
        with patch("urllib.request.urlopen", side_effect=self._raise(429)):
            self.assertEqual(handler.get_awards()["error"], "rate_limit_exceeded")

    def test_5xx_maps_to_source_unavailable_not_edgar(self):
        for code in (502, 503, 504):
            with patch("urllib.request.urlopen", side_effect=self._raise(code)):
                r = handler.get_opportunities()
            self.assertEqual(r["error"], "source_unavailable")
            self.assertNotIn("EDGAR", r["detail"])

    def test_network_error_is_caught(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            self.assertEqual(handler.get_grants()["error"], "network")


class TestResponseParsing(unittest.TestCase):
    def test_json_body_is_returned(self):
        payload = json.dumps({"total": 82, "opportunities": [{"title": "x"}]}).encode()
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            with patch("urllib.request.urlopen", return_value=_mock_response(payload)):
                r = handler.get_opportunities()
        self.assertEqual(r["total"], 82)

    def test_empty_body_returns_empty_dict(self):
        with patch.dict(os.environ, {"EDGRAPI_KEY": "edgr_test"}):
            with patch("urllib.request.urlopen", return_value=_mock_response(b"")):
                self.assertEqual(handler.get_grants(), {})


if __name__ == "__main__":
    unittest.main()
