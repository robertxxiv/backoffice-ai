from __future__ import annotations

import unittest

from app.core.config import get_settings
from app.embeddings.service import build_embedding_service
from app.retrieval.service import RetrievalService, compile_pgvector_statement


class RetrievalServiceTests(unittest.TestCase):
    def test_pgvector_statement_uses_cosine_distance_operator(self) -> None:
        settings = get_settings()
        service = RetrievalService(settings=settings, embedding_service=build_embedding_service(settings))
        statement = service.build_pgvector_statement(
            query_vector=[0.1] * settings.embedding_dimensions,
            score_threshold=0.2,
            limit=5,
        )
        compiled = compile_pgvector_statement(statement)
        self.assertIn("<=>", compiled)
        self.assertIn("ORDER BY", compiled)
        self.assertIn("LIMIT 5", compiled)


if __name__ == "__main__":
    unittest.main()
