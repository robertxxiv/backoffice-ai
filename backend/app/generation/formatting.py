from __future__ import annotations

from typing import Literal

from app.retrieval.schemas import RetrievedChunk

GenerationMode = Literal["standard", "activity_catalog"]

ACTIVITY_KEYWORDS = (
    "activity",
    "activities",
    "experience",
    "experiences",
    "things to do",
    "what can i do",
    "cosa fare",
    "attivita",
    "attività",
    "escurs",
    "tour",
    "brochure",
    "catalog",
    "catalogo",
)

CATALOG_CATEGORIES = {"travel_catalog", "activities_catalog"}


def select_generation_mode(query: str, chunks: list[RetrievedChunk]) -> GenerationMode:
    categories = {
        str(chunk.metadata.get("category", "")).strip().lower()
        for chunk in chunks
        if chunk.metadata.get("category")
    }
    if not categories.intersection(CATALOG_CATEGORIES):
        return "standard"

    lowered_query = query.lower()
    if any(keyword in lowered_query for keyword in ACTIVITY_KEYWORDS):
        return "activity_catalog"
    return "standard"
