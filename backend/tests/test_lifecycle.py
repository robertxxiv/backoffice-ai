from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class DocumentLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_reingest_same_source_is_upsert_and_noop_when_unchanged(self) -> None:
        first = self.client.post(
            "/ingest",
            json={
                "payload": "Norwegian VAT is 25 percent for consulting.",
                "metadata": {"country": "NO"},
                "source_name": "company-rules",
            },
        )
        second = self.client.post(
            "/ingest",
            json={
                "payload": "Norwegian VAT is 25 percent for consulting.",
                "metadata": {"country": "NO"},
                "source_name": "company-rules",
            },
        )
        first_payload = first.json()
        second_payload = second.json()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first_payload["document_id"], second_payload["document_id"])
        self.assertEqual(first_payload["version"], 1)
        self.assertEqual(second_payload["version"], 1)
        self.assertEqual(first_payload["lifecycle_action"], "created")
        self.assertEqual(second_payload["lifecycle_action"], "unchanged")

    def test_content_change_resets_index_state_and_increments_version(self) -> None:
        created = self.client.post(
            "/ingest",
            json={
                "payload": "Winter prices apply from December to February.",
                "metadata": {"season": "winter"},
                "source_name": "season-rules",
            },
        )
        document_id = created.json()["document_id"]
        reindex = self.client.post(
            "/reindex",
            json={
                "document_id": document_id,
                "run_inline": True,
                "strategy": "overlap",
                "chunk_size": 512,
                "overlap_tokens": 64,
            },
        )
        self.assertEqual(reindex.status_code, 202)
        updated = self.client.post(
            "/ingest",
            json={
                "payload": "Winter prices apply from November to February.",
                "metadata": {"season": "winter"},
                "source_name": "season-rules",
            },
        )
        updated_payload = updated.json()
        self.assertEqual(updated.status_code, 201)
        self.assertEqual(updated_payload["document_id"], document_id)
        self.assertEqual(updated_payload["version"], 2)
        self.assertEqual(updated_payload["lifecycle_action"], "updated")
        self.assertTrue(updated_payload["is_index_stale"])

        document = self.client.get(f"/documents/{document_id}")
        document_payload = document.json()
        self.assertEqual(document.status_code, 200)
        self.assertEqual(document_payload["status"], "ingested")
        self.assertEqual(document_payload["chunk_count"], 0)
        self.assertEqual(document_payload["embedding_count"], 0)
        self.assertEqual(document_payload["version"], 2)
        self.assertTrue(document_payload["is_index_stale"])

    def test_delete_document_removes_it(self) -> None:
        created = self.client.post(
            "/ingest",
            json={"payload": "temporary", "metadata": {}, "source_name": "delete-me"},
        )
        document_id = created.json()["document_id"]
        deleted = self.client.delete(f"/documents/{document_id}")
        self.assertEqual(deleted.status_code, 204)
        missing = self.client.get(f"/documents/{document_id}")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
