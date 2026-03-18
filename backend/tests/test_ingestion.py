from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class IngestionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()

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
        response = self.client.post("/ingest", files=files, data=data)
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
        )
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["metadata_summary"]["category"], "travel_catalog")
        self.assertEqual(payload["metadata_summary"]["type"], "travel_catalog")

    def test_rejects_unsupported_upload(self) -> None:
        files = {"file": ("notes.txt", b"plain text", "text/plain")}
        response = self.client.post("/ingest", files=files)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
