from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.main import app
from tests import auth_headers


class IngestionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()
        cls.headers = auth_headers(cls.client)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_healthcheck(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ingest_markdown_file(self) -> None:
        files = {"file": ("quote.md", b"# Quote\n\nSeasonal pricing applies.", "text/markdown")}
        data = {"metadata": '{"customer":"acme"}'}
        response = self.client.post("/ingest", files=files, data=data, headers=self.headers)
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["source_type"], "file")
        self.assertEqual(payload["metadata_summary"]["customer"], "acme")

    def test_ingest_json_payload(self) -> None:
        response = self.client.post(
            "/ingest",
            json={
                "payload": {
                    "service": {"name": "Audit", "vat": 25},
                    "season": "winter",
                },
                "metadata": {"source": "api"},
                "source_name": "pricing-dump",
            },
            headers=self.headers,
        )
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["source_type"], "payload")
        self.assertEqual(payload["source_ref"], "pricing-dump")

    def test_metadata_type_is_normalized_to_category(self) -> None:
        response = self.client.post(
            "/ingest",
            json={
                "payload": "Winter catalog for Northern Norway.",
                "metadata": {"type": "travel_catalog", "language": "it"},
                "source_name": "nordikae-catalog",
            },
            headers=self.headers,
        )
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["metadata_summary"]["category"], "travel_catalog")
        self.assertEqual(payload["metadata_summary"]["type"], "travel_catalog")

    def test_rejects_unsupported_upload(self) -> None:
        files = {"file": ("notes.txt", b"plain text", "text/plain")}
        response = self.client.post("/ingest", files=files, headers=self.headers)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()


class IngestionLimitTests(unittest.TestCase):
    def test_rejects_oversized_json_payload(self) -> None:
        application = create_app(
            Settings(
                auth_secret_key="test-auth-secret",
                initial_admin_email="admin@example.com",
                initial_admin_password="admin-password",
                trusted_hosts=["testserver"],
                max_ingest_json_bytes=64,
            )
        )
        with TestClient(application) as client:
            headers = auth_headers(client)
            response = client.post(
                "/ingest",
                json={
                    "payload": "x" * 256,
                    "metadata": {"source": "test"},
                    "source_name": "too-large-json",
                },
                headers=headers,
            )
        self.assertEqual(response.status_code, 413)
        self.assertIn("size limit", response.json()["detail"].lower())

    def test_rejects_oversized_file_upload(self) -> None:
        application = create_app(
            Settings(
                auth_secret_key="test-auth-secret",
                initial_admin_email="admin@example.com",
                initial_admin_password="admin-password",
                trusted_hosts=["testserver"],
                max_ingest_request_bytes=1024,
                max_upload_file_bytes=16,
            )
        )
        with TestClient(application) as client:
            headers = auth_headers(client)
            files = {"file": ("large.md", b"x" * 64, "text/markdown")}
            response = client.post("/ingest", files=files, headers=headers)
        self.assertEqual(response.status_code, 413)
        self.assertIn("size limit", response.json()["detail"].lower())
