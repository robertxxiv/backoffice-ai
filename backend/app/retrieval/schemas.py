from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_ref: str
    content: str
    score: float
    metadata: dict[str, Any]
