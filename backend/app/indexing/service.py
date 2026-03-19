from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.chunking.schemas import ChunkRequest
from app.chunking.service import ChunkingService
from app.core.config import Settings
from app.db.models import Document, IndexJob, User
from app.embeddings.service import EmbeddingService


class IndexingService:
    def __init__(
        self,
        settings: Settings,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
    ) -> None:
        self._settings = settings
        self._chunking_service = chunking_service
        self._embedding_service = embedding_service

    def create_jobs(
        self,
        session: Session,
        *,
        document_id: str | None,
        chunk_request: ChunkRequest,
        run_inline: bool,
        actor_user: User,
    ) -> list[IndexJob]:
        documents = (
            [session.get(Document, document_id)]
            if document_id
            else list(session.scalars(select(Document).order_by(Document.created_at.asc())))
        )
        if document_id and documents[0] is None:
            raise LookupError(f"Document '{document_id}' was not found.")
        filtered_documents = [document for document in documents if document is not None]
        if not filtered_documents:
            return []
        session.execute(
            delete(IndexJob).where(
                IndexJob.document_id.in_([document.id for document in filtered_documents]),
                IndexJob.status.in_(["pending", "failed", "superseded"]),
            )
        )
        jobs = [
            IndexJob(
                document_id=document.id,
                document_version=document.version,
                payload=chunk_request.model_dump(),
                status="pending",
                created_by_user_id=actor_user.id,
            )
            for document in filtered_documents
        ]
        session.add_all(jobs)
        for document in filtered_documents:
            document.status = "index_pending"
            document.index_error = None
        session.commit()
        if run_inline:
            for job in jobs:
                self.process_job(job.id, session)
            for job in jobs:
                session.refresh(job)
        return jobs

    def process_job(self, job_id: str, session: Session) -> IndexJob:
        job = session.get(IndexJob, job_id)
        if job is None:
            raise LookupError(f"Job '{job_id}' was not found.")
        if job.document_id is None:
            raise ValueError("Index job is missing document_id.")
        document = session.get(Document, job.document_id)
        if document is None:
            raise LookupError(f"Document '{job.document_id}' was not found.")
        if document.version != job.document_version:
            job.status = "superseded"
            job.error_message = "Skipped stale job for an older document version."
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
            return job
        try:
            document.status = "indexing"
            document.index_error = None
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            session.commit()
            chunk_request = ChunkRequest.model_validate(job.payload or {})
            self._chunking_service.create_chunks(job.document_id, chunk_request, session)
            self._embedding_service.embed_document_chunks(job.document_id, session)
            session.refresh(job)
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            session.refresh(document)
            document.status = "indexed"
            document.index_error = None
            document.last_indexed_at = datetime.now(timezone.utc)
            session.commit()
        except Exception as exc:
            session.refresh(job)
            session.refresh(document)
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            document.status = "index_failed"
            document.index_error = str(exc)
            session.commit()
            raise
        session.refresh(job)
        return job

    def process_pending_jobs(self, session: Session, limit: int = 10) -> int:
        jobs = list(
            session.scalars(
                select(IndexJob).where(IndexJob.status == "pending").order_by(IndexJob.created_at.asc()).limit(limit)
            )
        )
        processed = 0
        for job in jobs:
            try:
                self.process_job(job.id, session)
            except Exception:
                pass
            processed += 1
        return processed
