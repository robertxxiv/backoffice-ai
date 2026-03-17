from __future__ import annotations

from typing import Any

from sqlalchemy import Select, cast, literal, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Chunk, Document, Embedding
from app.db.vector import cosine_similarity
from app.embeddings.service import EmbeddingService
from app.retrieval.schemas import RetrievedChunk
from pgvector.sqlalchemy import Vector


class RetrievalService:
    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self.mode = "python_fallback"

    def search(
        self,
        *,
        query: str,
        session: Session,
        top_k: int | None = None,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self._embedding_service._provider.embed_texts([query])[0]
        threshold = self._settings.retrieval_score_threshold if score_threshold is None else score_threshold
        desired = self._settings.default_top_k if top_k is None else top_k
        if session.bind is not None and session.bind.dialect.name == "postgresql":
            self.mode = "pgvector"
            retrieved = self._search_postgres(session, query_vector, threshold, filters)
            return _deduplicate(retrieved, desired)
        self.mode = "python_fallback"
        retrieved = self._search_fallback(session, query_vector, threshold, filters)
        return _deduplicate(retrieved, desired)

    def build_pgvector_statement(
        self,
        *,
        query_vector: list[float],
        score_threshold: float,
        limit: int,
    ) -> Select[tuple[Chunk, Document, float]]:
        vector_column = cast(Embedding.vector, Vector(self._settings.embedding_dimensions))
        distance_expression = vector_column.cosine_distance(query_vector)
        score_expression = (literal(1.0) - distance_expression).label("score")
        return (
            select(Chunk, Document, score_expression)
            .join(Embedding, Embedding.chunk_id == Chunk.id)
            .join(Document, Chunk.document_id == Document.id)
            .where(distance_expression <= (1.0 - score_threshold))
            .order_by(distance_expression.asc())
            .limit(limit)
        )

    def _search_postgres(
        self,
        session: Session,
        query_vector: list[float],
        score_threshold: float,
        filters: dict[str, Any] | None,
    ) -> list[RetrievedChunk]:
        candidate_limit = max(self._settings.retrieval_candidate_limit, self._settings.default_top_k)
        rows = session.execute(
            self.build_pgvector_statement(
                query_vector=query_vector,
                score_threshold=score_threshold,
                limit=candidate_limit,
            )
        ).all()
        return [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                document_ref=document.source_ref,
                content=chunk.content,
                score=float(score),
                metadata={**document.document_metadata, **chunk.chunk_metadata},
            )
            for chunk, document, score in rows
            if _matches_filters({**document.document_metadata, **chunk.chunk_metadata}, filters)
        ]

    def _search_fallback(
        self,
        session: Session,
        query_vector: list[float],
        score_threshold: float,
        filters: dict[str, Any] | None,
    ) -> list[RetrievedChunk]:
        rows = session.execute(
            select(Embedding, Chunk, Document)
            .join(Chunk, Embedding.chunk_id == Chunk.id)
            .join(Document, Chunk.document_id == Document.id)
        ).all()
        retrieved = [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                document_ref=document.source_ref,
                content=chunk.content,
                score=cosine_similarity(query_vector, embedding.vector),
                metadata={**document.document_metadata, **chunk.chunk_metadata},
            )
            for embedding, chunk, document in rows
            if _matches_filters({**document.document_metadata, **chunk.chunk_metadata}, filters)
        ]
        retrieved.sort(key=lambda item: item.score, reverse=True)
        return [item for item in retrieved if item.score >= score_threshold]


def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    return all(metadata.get(key) == value for key, value in filters.items())


def _deduplicate(items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    seen: set[tuple[str, str]] = set()
    results: list[RetrievedChunk] = []
    for item in items:
        key = (item.document_id, item.content[:160])
        if key in seen:
            continue
        seen.add(key)
        results.append(item)
        if len(results) >= top_k:
            break
    return results


def compile_pgvector_statement(statement: Select[object]) -> str:
    return str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
