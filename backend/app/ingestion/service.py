from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Chunk, Document, Embedding, IndexJob
from app.ingestion.extractors import detect_content_type, extract_payload_text, extract_text
from app.ingestion.normalizers import normalize_text
from app.ingestion.schemas import ExtractedDocument, IngestRequest, IngestResponse


class IngestionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def ingest_file(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        data: bytes,
        metadata: dict[str, Any],
        session: Session,
    ) -> IngestResponse:
        resolved_type = detect_content_type(filename, content_type)
        content = extract_text(data, resolved_type)
        extracted = ExtractedDocument(
            source_type="file",
            source_ref=filename or "upload",
            content_type=resolved_type,
            content=content,
            metadata=metadata,
        )
        return self._persist(extracted, session)

    def ingest_request(self, request: IngestRequest, session: Session) -> IngestResponse:
        if request.url is not None:
            extracted = self._fetch_url(str(request.url), request.metadata)
            return self._persist(extracted, session)
        payload_text = extract_payload_text(request.payload)
        extracted = ExtractedDocument(
            source_type="payload",
            source_ref=request.source_name or "payload",
            content_type="application/json" if not isinstance(request.payload, str) else "text/plain",
            content=payload_text,
            metadata=request.metadata,
        )
        return self._persist(extracted, session)

    def _fetch_url(self, url: str, metadata: dict[str, Any]) -> ExtractedDocument:
        response = httpx.get(url, timeout=self._settings.request_timeout_seconds, follow_redirects=True)
        response.raise_for_status()
        content_type = detect_content_type(url, response.headers.get("content-type"))
        content = extract_text(response.content, content_type)
        return ExtractedDocument(
            source_type="url",
            source_ref=url,
            content_type=content_type,
            content=content,
            metadata=metadata,
        )

    def _persist(self, extracted: ExtractedDocument, session: Session) -> IngestResponse:
        normalized_content = normalize_text(extracted.content)
        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        existing = session.scalar(
            select(Document).where(
                Document.source_type == extracted.source_type,
                Document.source_ref == extracted.source_ref,
            )
        )
        if existing is None:
            document = Document(
                source_type=extracted.source_type,
                source_ref=extracted.source_ref,
                content_type=extracted.content_type,
                content_hash=content_hash,
                content=normalized_content,
                document_metadata=extracted.metadata,
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            return _build_ingest_response(document, lifecycle_action="created")
        if existing.content_hash == content_hash:
            changed_metadata = existing.document_metadata != extracted.metadata
            changed_type = existing.content_type != extracted.content_type
            if changed_metadata or changed_type:
                existing.document_metadata = extracted.metadata
                existing.content_type = extracted.content_type
                session.commit()
                session.refresh(existing)
                return _build_ingest_response(existing, lifecycle_action="updated")
            return _build_ingest_response(existing, lifecycle_action="unchanged")
        self._purge_index_state(existing.id, session)
        existing.content = normalized_content
        existing.content_hash = content_hash
        existing.content_type = extracted.content_type
        existing.document_metadata = extracted.metadata
        existing.version += 1
        existing.status = "ingested"
        existing.index_error = None
        existing.last_ingested_at = _utcnow()
        existing.last_indexed_at = None
        session.commit()
        session.refresh(existing)
        return _build_ingest_response(existing, lifecycle_action="updated")

    def delete_document(self, document_id: str, session: Session) -> None:
        document = session.get(Document, document_id)
        if document is None:
            raise LookupError(f"Document '{document_id}' was not found.")
        self._purge_index_state(document.id, session)
        session.execute(delete(IndexJob).where(IndexJob.document_id == document.id))
        session.delete(document)
        session.commit()

    def _purge_index_state(self, document_id: str, session: Session) -> None:
        chunk_ids = list(session.scalars(select(Chunk.id).where(Chunk.document_id == document_id)))
        if chunk_ids:
            session.execute(delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids)))
        session.execute(delete(Chunk).where(Chunk.document_id == document_id))
        session.execute(
            delete(IndexJob).where(
                IndexJob.document_id == document_id,
                IndexJob.status.in_(["pending", "running", "failed", "superseded"]),
            )
        )
        session.flush()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_ingest_response(document: Document, lifecycle_action: str) -> IngestResponse:
    return IngestResponse(
        document_id=document.id,
        source_type=document.source_type,
        source_ref=document.source_ref,
        version=document.version,
        status=document.status,
        lifecycle_action=lifecycle_action,
        content_length=len(document.content),
        metadata_summary=document.document_metadata,
        last_ingested_at=document.last_ingested_at,
        last_indexed_at=document.last_indexed_at,
        is_index_stale=_is_index_stale(document),
    )


def _is_index_stale(document: Document) -> bool:
    if document.last_indexed_at is None:
        return True
    return document.last_indexed_at < document.last_ingested_at or document.status != "indexed"
