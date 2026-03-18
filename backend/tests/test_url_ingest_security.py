from __future__ import annotations

import unittest
from ipaddress import ip_address
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.ingestion.url_guard import SafeUrlFetcher
from app.main import app


class FakeHttpClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)

    def __enter__(self) -> "FakeHttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, _: str) -> httpx.Response:
        if not self._responses:
            raise AssertionError("Unexpected HTTP call in test.")
        return self._responses.pop(0)


class UrlIngestSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_blocks_loopback_ip_ingest(self) -> None:
        response = self.client.post("/ingest", json={"url": "http://127.0.0.1/private"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("blocked", response.json()["detail"].lower())

    def test_blocks_private_hostname_resolution(self) -> None:
        with patch.object(SafeUrlFetcher, "_resolve_ip_addresses", return_value={ip_address("10.0.0.5")}):
            response = self.client.post("/ingest", json={"url": "http://internal.example.test/report"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("private", response.json()["detail"].lower())

    def test_blocks_redirect_to_private_target(self) -> None:
        fetcher = SafeUrlFetcher(Settings())
        responses = [
            httpx.Response(
                302,
                headers={"location": "http://127.0.0.1/secret"},
                request=httpx.Request("GET", "https://93.184.216.34/start"),
            )
        ]
        with (
            patch("app.ingestion.url_guard.httpx.Client", return_value=FakeHttpClient(responses)),
        ):
            with self.assertRaises(ValueError):
                fetcher.fetch("https://93.184.216.34/start")

    def test_allows_public_allowlisted_domain(self) -> None:
        settings = Settings(url_ingest_allowed_domains=["example.com"])
        fetcher = SafeUrlFetcher(settings)
        responses = [
            httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=b"<html><body>ok</body></html>",
                request=httpx.Request("GET", "https://docs.example.com/page"),
            )
        ]
        with (
            patch.object(SafeUrlFetcher, "_resolve_ip_addresses", return_value={ip_address("93.184.216.34")}),
            patch("app.ingestion.url_guard.httpx.Client", return_value=FakeHttpClient(responses)),
        ):
            final_url, response = fetcher.fetch("https://docs.example.com/page")
        self.assertEqual(final_url, "https://docs.example.com/page")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
