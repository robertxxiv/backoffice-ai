from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.chunking.schemas import ChunkBatchResponse, ChunkRecord, ChunkRequest
from app.chunking.strategies import build_chunks
from app.db.models import Chunk, Document, Embedding


class ChunkingService:
    def create_chunks(self, document_id: str, request: ChunkRequest, session: Session) -> ChunkBatchResponse:
        document = self._get_document(document_id, session)
        candidates = build_chunks(document.id, document.content, document.source_ref, request)
        chunk_ids = list(session.scalars(select(Chunk.id).where(Chunk.document_id == document.id)))
        if chunk_ids:
            session.execute(delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids)))
        session.execute(delete(Chunk).where(Chunk.document_id == document.id))
        persisted = [
            Chunk(
                document_id=document.id,
                chunk_index=item.chunk_index,
                strategy=item.strategy,
                token_count=item.token_count,
                section=item.section,
                content=item.content,
                chunk_metadata={**document.document_metadata, **item.metadata},
            )
            for item in candidates
        ]
        session.add_all(persisted)
        document.status = "chunked"
        document.last_indexed_at = None
        document.index_error = None
        session.commit()
        return self.list_chunks(document.id, session)

    def list_chunks(self, document_id: str, session: Session) -> ChunkBatchResponse:
        document = self._get_document(document_id, session)
        chunks = list(
            session.scalars(
                select(Chunk).where(Chunk.document_id == document.id).order_by(Chunk.chunk_index.asc())
            )
        )
        strategy = chunks[0].strategy if chunks else "fixed"
        overlap_tokens = _read_overlap_tokens(chunks)
        chunk_size = max((chunk.token_count for chunk in chunks), default=0)
        return ChunkBatchResponse(
            document_id=document.id,
            chunk_count=len(chunks),
            strategy=strategy,
            chunk_size=chunk_size,
            overlap_tokens=overlap_tokens,
            chunks=[
                ChunkRecord(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    strategy=chunk.strategy,
                    token_count=chunk.token_count,
                    section=chunk.section,
                    source_ref=document.source_ref,
                    content=chunk.content,
                    metadata_summary=chunk.chunk_metadata,
                )
                for chunk in chunks
            ],
        )

    def _get_document(self, document_id: str, session: Session) -> Document:
        document = session.get(Document, document_id)
        if document is None:
            raise LookupError(f"Document '{document_id}' was not found.")
        return document


def _read_overlap_tokens(chunks: list[Chunk]) -> int:
    if not chunks:
        return 0
    overlap = chunks[0].chunk_metadata.get("overlap_tokens", 0)
    return int(overlap) if isinstance(overlap, int) else 0
