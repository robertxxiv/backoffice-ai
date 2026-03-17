from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.chunking.tokenizer import encode_text
from app.main import app


class ChunkingApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_manager = TestClient(app)
        cls.client = cls.client_manager.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_manager.__exit__(None, None, None)

    def test_create_fixed_chunks(self) -> None:
        document_id = self._ingest_large_document()
        response = self.client.post(
            f"/documents/{document_id}/chunks",
            json={"strategy": "fixed", "chunk_size": 512},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertGreater(payload["chunk_count"], 1)
        self.assertTrue(all(chunk["token_count"] <= 512 for chunk in payload["chunks"]))

    def test_create_overlap_chunks(self) -> None:
        document_id = self._ingest_large_document()
        response = self.client.post(
            f"/documents/{document_id}/chunks",
            json={"strategy": "overlap", "chunk_size": 512, "overlap_tokens": 64},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(payload["chunk_count"], 2)
        first_tokens = encode_text(payload["chunks"][0]["content"])
        second_tokens = encode_text(payload["chunks"][1]["content"])
        self.assertEqual(first_tokens[-64:], second_tokens[:64])

    def test_missing_document_returns_404(self) -> None:
        response = self.client.post(
            "/documents/missing-document/chunks",
            json={"strategy": "fixed", "chunk_size": 512},
        )
        self.assertEqual(response.status_code, 404)

    def _ingest_large_document(self) -> str:
        text = " ".join(f"token{i}" for i in range(1300))
        response = self.client.post(
            "/ingest",
            json={"payload": text, "metadata": {"source": "test"}, "source_name": "long-doc"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["document_id"]


if __name__ == "__main__":
    unittest.main()
