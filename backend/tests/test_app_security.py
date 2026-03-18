from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class AppSecurityTests(unittest.TestCase):
    def test_docs_disabled_by_default(self) -> None:
        application = create_app(Settings(enable_api_docs=False, trusted_hosts=["testserver"]))
        with TestClient(application) as client:
            response = client.get("/docs")
        self.assertEqual(response.status_code, 404)

    def test_docs_can_be_enabled(self) -> None:
        application = create_app(Settings(enable_api_docs=True, trusted_hosts=["testserver"]))
        with TestClient(application) as client:
            response = client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_untrusted_host_is_rejected(self) -> None:
        application = create_app(Settings(enable_api_docs=False, trusted_hosts=["allowed.example"]))
        with TestClient(application) as client:
            response = client.get("/health", headers={"host": "blocked.example"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid host", response.text.lower())

    def test_cors_allows_only_explicit_origins_by_default(self) -> None:
        application = create_app(
            Settings(
                trusted_hosts=["testserver"],
                cors_origins=["http://localhost:3000"],
                cors_origin_regex="",
                cors_allow_credentials=False,
            )
        )
        with TestClient(application) as client:
            allowed = client.options(
                "/health",
                headers={
                    "origin": "http://localhost:3000",
                    "access-control-request-method": "GET",
                    "host": "testserver",
                },
            )
            blocked = client.options(
                "/health",
                headers={
                    "origin": "http://172.16.5.48:3000",
                    "access-control-request-method": "GET",
                    "host": "testserver",
                },
            )

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(
            allowed.headers.get("access-control-allow-origin"),
            "http://localhost:3000",
        )
        self.assertIsNone(blocked.headers.get("access-control-allow-origin"))

    def test_cors_credentials_are_opt_in(self) -> None:
        application = create_app(
            Settings(
                trusted_hosts=["testserver"],
                cors_origins=["http://localhost:3000"],
                cors_allow_credentials=False,
            )
        )
        with TestClient(application) as client:
            response = client.options(
                "/health",
                headers={
                    "origin": "http://localhost:3000",
                    "access-control-request-method": "GET",
                    "host": "testserver",
                },
            )

        self.assertNotIn("access-control-allow-credentials", response.headers)


if __name__ == "__main__":
    unittest.main()
