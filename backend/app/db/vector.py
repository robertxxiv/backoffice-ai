from __future__ import annotations

import math
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    Vector = None


class EmbeddingVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            dimensions = get_settings().embedding_dimensions
            return dialect.type_descriptor(Vector(dimensions))
        return dialect.type_descriptor(JSON())


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)
