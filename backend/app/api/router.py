from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.schemas import (
    DocumentDetail,
    DocumentSummary,
    JobResponse,
    QueryRequest,
    QueryResponse,
    QuerySource,
    QueryTrace,
    ReindexRequest,
    ReindexResponse,
)
from app.auth.dependencies import get_admin_user, get_current_user
from app.auth.schemas import CreateUserRequest, LoginRequest, LoginResponse, UserResponse
from app.auth.security import create_access_token
from app.auth.service import authenticate_user, create_user
from app.chunking.schemas import ChunkBatchResponse, ChunkRequest
from app.chunking.service import ChunkingService
from app.core.config import Settings, get_settings
from app.db.models import Chunk, Document, Embedding, IndexJob, QueryLog, User
from app.db.session import get_session
from app.embeddings.service import build_embedding_service
from app.generation.service import build_generation_service
from app.indexing.service import IndexingService
from app.ingestion.schemas import IngestRequest, IngestResponse
from app.ingestion.service import IngestionService
from app.metadata import normalize_metadata
from app.providers.errors import ProviderRequestError
from app.retrieval.service import RetrievalService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ingestion_service(settings: Settings = Depends(get_settings)) -> IngestionService:
    return IngestionService(settings)


def get_chunking_service() -> ChunkingService:
    return ChunkingService()


def get_indexing_service(settings: Settings = Depends(get_settings)) -> IndexingService:
    return IndexingService(
        settings=settings,
        chunking_service=ChunkingService(),
        embedding_service=build_embedding_service(settings),
    )


def get_retrieval_service(settings: Settings = Depends(get_settings)) -> RetrievalService:
    embedding_service = build_embedding_service(settings)
    return RetrievalService(settings=settings, embedding_service=embedding_service)


@router.get("/health")
def healthcheck(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "ok",
        "embedding_provider": settings.embedding_provider,
        "generation_provider": settings.generation_provider,
        "api_docs_enabled": settings.enable_api_docs,
        "upload_limits": {
            "file_bytes": settings.max_upload_file_bytes,
            "request_bytes": settings.max_ingest_request_bytes,
            "json_bytes": settings.max_ingest_json_bytes,
        },
    }


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> LoginResponse:
    if not settings.auth_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on this deployment.",
        )
    user = authenticate_user(session, str(payload.email), payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return LoginResponse(
        access_token=create_access_token(
            user_id=user.id,
            role=user.role,
            secret_key=settings.auth_secret_key,
            ttl_minutes=settings.access_token_ttl_minutes,
        ),
        user=_user_response(user),
    )


@router.get("/auth/me", response_model=UserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.get("/auth/users", response_model=list[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(get_admin_user),
) -> list[UserResponse]:
    users = list(session.scalars(select(User).order_by(User.created_at.asc())))
    return [_user_response(user) for user in users]


@router.post("/auth/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_account(
    payload: CreateUserRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_admin_user),
) -> UserResponse:
    try:
        user = create_user(session, email=payload.email, password=payload.password, role=payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _user_response(user)


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    request: Request,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
    service: IngestionService = Depends(get_ingestion_service),
    current_user: User = Depends(get_current_user),
) -> IngestResponse:
    content_type = request.headers.get("content-type", "")
    try:
        if content_type.startswith("multipart/form-data"):
            _enforce_content_length_limit(
                request,
                settings.max_ingest_request_bytes,
                "The upload request exceeds the configured size limit.",
            )
            return await _handle_form_ingest(
                request,
                service,
                session,
                settings.max_upload_file_bytes,
                current_user,
            )
        if content_type.startswith("application/json"):
            payload = await _parse_json_ingest_request(request, settings.max_ingest_json_bytes)
            return service.ingest_request(payload, session, current_user)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Use multipart/form-data or application/json.",
    )


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[DocumentSummary]:
    documents = list(session.scalars(select(Document).order_by(Document.created_at.desc())))
    return [_document_summary(document, session) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DocumentDetail:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    summary = _document_summary(document, session)
    return DocumentDetail(
        **summary.model_dump(),
        content_type=document.content_type,
        content_preview=document.content[:500],
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_document(
    document_id: str,
    session: Session = Depends(get_session),
    service: IngestionService = Depends(get_ingestion_service),
    _: User = Depends(get_admin_user),
) -> Response:
    try:
        service.delete_document(document_id, session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/documents/{document_id}/chunks",
    response_model=ChunkBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_chunks(
    document_id: str,
    payload: ChunkRequest,
    session: Session = Depends(get_session),
    service: ChunkingService = Depends(get_chunking_service),
    _: User = Depends(get_current_user),
) -> ChunkBatchResponse:
    try:
        return service.create_chunks(document_id, payload, session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/documents/{document_id}/chunks", response_model=ChunkBatchResponse)
def list_document_chunks(
    document_id: str,
    session: Session = Depends(get_session),
    service: ChunkingService = Depends(get_chunking_service),
    _: User = Depends(get_current_user),
) -> ChunkBatchResponse:
    try:
        return service.list_chunks(document_id, session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/reindex", response_model=ReindexResponse, status_code=status.HTTP_202_ACCEPTED)
def reindex_documents(
    payload: ReindexRequest,
    session: Session = Depends(get_session),
    service: IndexingService = Depends(get_indexing_service),
    current_user: User = Depends(get_current_user),
) -> ReindexResponse:
    chunk_request = ChunkRequest(
        strategy=payload.strategy,
        chunk_size=payload.chunk_size,
        overlap_tokens=payload.overlap_tokens,
    )
    try:
        jobs = service.create_jobs(
            session,
            document_id=payload.document_id,
            chunk_request=chunk_request,
            run_inline=payload.run_inline,
            actor_user=current_user,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ReindexResponse(jobs=[_job_response(job) for job in jobs])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_admin_user),
) -> JobResponse:
    job = session.get(IndexJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return _job_response(job)


@router.post("/query", response_model=QueryResponse)
def query_documents(
    payload: QueryRequest,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    try:
        chunks = retrieval_service.search(
            query=payload.query,
            session=session,
            top_k=payload.top_k,
            score_threshold=payload.score_threshold,
            filters=payload.filters,
        )
        generation_service = build_generation_service(settings)
        generated = generation_service.generate_answer(payload.query, chunks)
    except Exception as exc:  # noqa: BLE001
        _raise_query_exception(exc)
    cited_ids = {
        citation
        for citation in generated.get("citations", [])
        if isinstance(citation, str)
    }
    sources = [
        QuerySource(
            document=chunk.document_ref,
            chunk=chunk.chunk_id,
            score=round(chunk.score, 4),
            excerpt=chunk.content[:240],
            metadata=chunk.metadata,
        )
        for chunk in chunks
        if not cited_ids or chunk.chunk_id in cited_ids
    ]
    response = QueryResponse(
        answer=str(generated["answer"]),
        sources=sources,
        trace=QueryTrace(
            top_k=payload.top_k,
            threshold=payload.score_threshold
            if payload.score_threshold is not None
            else settings.retrieval_score_threshold,
            retrieval_count=len(chunks),
            retrieval_mode=retrieval_service.mode,
            embedding_provider=settings.embedding_provider,
            generation_provider=settings.generation_provider,
        ),
        machine_output=generated.get("machine_output"),
    )
    session.add(
        QueryLog(
            query_text=payload.query,
            top_k=response.trace.top_k,
            threshold=response.trace.threshold,
            answer=response.answer,
            sources=[item.model_dump() for item in response.sources],
            created_by_user_id=current_user.id,
        )
    )
    session.commit()
    return response


def _raise_query_exception(exc: Exception) -> None:
    logger.exception("query_request_failed")
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if isinstance(exc, ProviderRequestError):
        logger.error("provider_request_error stage=%s reason=%s", exc.stage, exc.reason)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
    if isinstance(exc, httpx.HTTPError) or exc.__class__.__module__.startswith("openai"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "The AI provider request failed unexpectedly. "
                "Check the API logs for the failing provider stage."
            ),
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The query could not be completed. Check the API logs for details.",
    ) from exc


async def _handle_form_ingest(
    request: Request,
    service: IngestionService,
    session: Session,
    max_upload_file_bytes: int,
    current_user: User,
) -> IngestResponse:
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "read") or not hasattr(upload, "filename"):
        raise ValueError("Form uploads must include a 'file' field.")
    metadata = _parse_metadata(form.get("metadata"))
    try:
        data = await _read_upload_with_limit(upload, max_upload_file_bytes)
        return service.ingest_file(
            filename=upload.filename,
            content_type=getattr(upload, "content_type", None),
            data=data,
            metadata=metadata,
            session=session,
            current_user=current_user,
        )
    finally:
        await upload.close()


def _parse_metadata(raw_value: Any) -> dict[str, Any]:
    if raw_value in (None, ""):
        return {}
    if not isinstance(raw_value, str):
        raise ValueError("metadata must be a JSON object encoded as a string.")
    parsed = json.loads(raw_value)
    if not isinstance(parsed, dict):
        raise ValueError("metadata must decode to a JSON object.")
    return parsed


async def _parse_json_ingest_request(request: Request, max_bytes: int) -> IngestRequest:
    raw_body = await request.body()
    if len(raw_body) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The JSON ingest payload exceeds the configured size limit.",
        )
    return IngestRequest.model_validate(json.loads(raw_body))


def _enforce_content_length_limit(request: Request, max_bytes: int, detail: str) -> None:
    raw_length = request.headers.get("content-length")
    if raw_length is None:
        return
    try:
        content_length = int(raw_length)
    except ValueError:
        return
    if content_length > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)


async def _read_upload_with_limit(upload: Any, max_bytes: int) -> bytes:
    data = bytearray()
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="The uploaded file exceeds the configured size limit.",
            )


def _document_summary(document: Document, session: Session) -> DocumentSummary:
    chunk_count = session.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document.id)) or 0
    embedding_count = (
        session.scalar(
            select(func.count())
            .select_from(Embedding)
            .join(Chunk, Embedding.chunk_id == Chunk.id)
            .where(Chunk.document_id == document.id)
        )
        or 0
    )
    return DocumentSummary(
        id=document.id,
        source_type=document.source_type,
        source_ref=document.source_ref,
        version=document.version,
        status=document.status,
        metadata_summary=normalize_metadata(document.document_metadata),
        chunk_count=int(chunk_count),
        embedding_count=int(embedding_count),
        last_ingested_at=document.last_ingested_at,
        last_indexed_at=document.last_indexed_at,
        is_index_stale=_is_index_stale(document),
        index_error=document.index_error,
        created_at=document.created_at,
    )


def _job_response(job: IndexJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        document_id=job.document_id,
        document_version=job.document_version,
        job_type=job.job_type,
        status=job.status,
        payload=job.payload,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _is_index_stale(document: Document) -> bool:
    if document.last_indexed_at is None:
        return True
    return document.last_indexed_at < document.last_ingested_at or document.status != "indexed"
