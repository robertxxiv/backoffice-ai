from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.chunking.schemas import ChunkStrategy


class DocumentSummary(BaseModel):
    id: str
    source_type: str
    source_ref: str
    version: int
    status: str
    metadata_summary: dict[str, Any]
    chunk_count: int
    embedding_count: int
    last_ingested_at: datetime
    last_indexed_at: datetime | None
    is_index_stale: bool
    index_error: str | None
    created_at: datetime


class DocumentDetail(DocumentSummary):
    content_type: str
    content_preview: str


class ReindexRequest(BaseModel):
    document_id: str | None = None
    run_inline: bool = False
    strategy: ChunkStrategy = "overlap"
    chunk_size: int = Field(default=512, ge=300, le=800)
    overlap_tokens: int = Field(default=64, ge=0, le=100)


class JobResponse(BaseModel):
    id: str
    document_id: str | None
    document_version: int
    job_type: str
    status: str
    payload: dict[str, Any]
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ReindexResponse(BaseModel):
    jobs: list[JobResponse]


class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class QuerySource(BaseModel):
    document: str
    chunk: str
    score: float
    excerpt: str
    metadata: dict[str, Any]


class QueryTrace(BaseModel):
    top_k: int
    threshold: float
    retrieval_count: int
    retrieval_mode: str
    embedding_provider: str
    generation_provider: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[QuerySource]
    trace: QueryTrace
