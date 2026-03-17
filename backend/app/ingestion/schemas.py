from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class IngestRequest(BaseModel):
    url: HttpUrl | None = None
    payload: dict[str, Any] | list[Any] | str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_name: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_source(self) -> "IngestRequest":
        provided = [self.url is not None, self.payload is not None]
        if sum(provided) != 1:
            raise ValueError("Provide exactly one of 'url' or 'payload'.")
        return self


class IngestResponse(BaseModel):
    document_id: str
    source_type: Literal["file", "url", "payload"]
    source_ref: str
    version: int
    status: str
    lifecycle_action: Literal["created", "updated", "unchanged"]
    content_length: int
    metadata_summary: dict[str, Any]
    last_ingested_at: datetime
    last_indexed_at: datetime | None
    is_index_stale: bool


@dataclass(slots=True)
class ExtractedDocument:
    source_type: Literal["file", "url", "payload"]
    source_ref: str
    content_type: str
    content: str
    metadata: dict[str, Any]
