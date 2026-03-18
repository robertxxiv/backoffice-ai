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


if __name__ == "__main__":
    unittest.main()
