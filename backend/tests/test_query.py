from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.providers.errors import ProviderRequestError
from tests import auth_headers


class QueryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()
        cls.headers = auth_headers(cls.client)

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
            headers=self.headers,
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
            headers=self.headers,
        )
        self.assertEqual(reindex_response.status_code, 202)
        self.assertEqual(reindex_response.json()["jobs"][0]["status"], "completed")

        query_response = self.client.post(
            "/query",
            json={"query": "What VAT applies to consulting in Norway?", "filters": {"country": "NO"}},
            headers=self.headers,
        )
        payload = query_response.json()
        self.assertEqual(query_response.status_code, 200)
        self.assertTrue(payload["sources"])
        self.assertEqual(payload["trace"]["retrieval_count"], 1)
        self.assertEqual(payload["trace"]["retrieval_mode"], "python_fallback")

        document_response = self.client.get(f"/documents/{document_id}", headers=self.headers)
        document_payload = document_response.json()
        self.assertEqual(document_response.status_code, 200)
        self.assertEqual(document_payload["status"], "indexed")
        self.assertGreaterEqual(document_payload["chunk_count"], 1)
        self.assertGreaterEqual(document_payload["embedding_count"], 1)

    def test_query_accepts_category_filter_for_type_metadata(self) -> None:
        ingest_response = self.client.post(
            "/ingest",
            json={
                "payload": "The winter travel catalog includes Tromso and Alta packages.",
                "metadata": {"type": "travel_catalog", "language": "it"},
                "source_name": "travel-catalog",
            },
            headers=self.headers,
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
            headers=self.headers,
        )
        self.assertEqual(reindex_response.status_code, 202)

        query_response = self.client.post(
            "/query",
            json={"query": "Which destinations are in the travel catalog?", "filters": {"category": "travel_catalog"}},
            headers=self.headers,
        )
        payload = query_response.json()
        self.assertEqual(query_response.status_code, 200)
        self.assertTrue(payload["sources"])
        self.assertEqual(payload["sources"][0]["metadata"]["category"], "travel_catalog")

    def test_query_returns_json_error_when_generation_fails(self) -> None:
        class FailingGenerationService:
            def generate_answer(self, query: str, chunks: list[object]) -> dict[str, object]:
                raise RuntimeError("generation exploded")

        with patch("app.api.router.build_generation_service", return_value=FailingGenerationService()):
            response = self.client.post(
                "/query",
                json={"query": "What is in the catalog?", "top_k": 5, "filters": {}},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "The query could not be completed. Check the API logs for details.",
        )

    def test_query_returns_specific_provider_timeout_message(self) -> None:
        class FailingGenerationService:
            def generate_answer(self, query: str, chunks: list[object]) -> dict[str, object]:
                raise ProviderRequestError(
                    stage="generation",
                    reason="timeout",
                    message="The answer generation request timed out. Try a shorter question or retry shortly.",
                )

        with patch("app.api.router.build_generation_service", return_value=FailingGenerationService()):
            response = self.client.post(
                "/query",
                json={"query": "What is in the catalog?", "top_k": 5, "filters": {}},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "The answer generation request timed out. Try a shorter question or retry shortly.",
        )


if __name__ == "__main__":
    unittest.main()
