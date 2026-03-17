from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class QueryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_inline_reindex_and_query(self) -> None:
        ingest_response = self.client.post(
            "/ingest",
            json={
                "payload": (
                    "Norwegian VAT for consulting is 25 percent. "
                    "Winter season pricing applies from December to February."
                ),
                "metadata": {"domain": "quotes", "country": "NO"},
                "source_name": "pricing-rules",
            },
        )
        self.assertEqual(ingest_response.status_code, 201)
        document_id = ingest_response.json()["document_id"]

        reindex_response = self.client.post(
            "/reindex",
            json={
                "document_id": document_id,
                "run_inline": True,
                "strategy": "overlap",
                "chunk_size": 512,
                "overlap_tokens": 64,
            },
        )
        self.assertEqual(reindex_response.status_code, 202)
        self.assertEqual(reindex_response.json()["jobs"][0]["status"], "completed")

        query_response = self.client.post(
            "/query",
            json={"query": "What VAT applies to consulting in Norway?", "filters": {"country": "NO"}},
        )
        payload = query_response.json()
        self.assertEqual(query_response.status_code, 200)
        self.assertTrue(payload["sources"])
        self.assertEqual(payload["trace"]["retrieval_count"], 1)
        self.assertEqual(payload["trace"]["retrieval_mode"], "python_fallback")

        document_response = self.client.get(f"/documents/{document_id}")
        document_payload = document_response.json()
        self.assertEqual(document_response.status_code, 200)
        self.assertEqual(document_payload["status"], "indexed")
        self.assertGreaterEqual(document_payload["chunk_count"], 1)
        self.assertGreaterEqual(document_payload["embedding_count"], 1)


if __name__ == "__main__":
    unittest.main()
