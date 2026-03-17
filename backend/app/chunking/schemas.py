from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ChunkStrategy = Literal["fixed", "overlap"]


class ChunkRequest(BaseModel):
    strategy: ChunkStrategy = "fixed"
    chunk_size: int = Field(default=512, ge=300, le=800)
    overlap_tokens: int = Field(default=64, ge=0, le=100)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_strategy(self) -> "ChunkRequest":
        if self.strategy == "fixed":
            self.overlap_tokens = 0
        if self.strategy == "overlap" and self.overlap_tokens < 50:
            raise ValueError("overlap_tokens must be between 50 and 100 for overlap strategy.")
        if self.overlap_tokens >= self.chunk_size:
            raise ValueError("overlap_tokens must be smaller than chunk_size.")
        return self


class ChunkRecord(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    strategy: ChunkStrategy
    token_count: int
    section: str | None
    source_ref: str
    content: str
    metadata_summary: dict[str, Any]


class ChunkBatchResponse(BaseModel):
    document_id: str
    chunk_count: int
    strategy: ChunkStrategy
    chunk_size: int
    overlap_tokens: int
    chunks: list[ChunkRecord]


@dataclass(slots=True)
class ChunkCandidate:
    chunk_index: int
    content: str
    token_count: int
    strategy: ChunkStrategy
    section: str | None
    metadata: dict[str, Any]
