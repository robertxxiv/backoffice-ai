from __future__ import annotations

from typing import Any


def normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(metadata)
    category = _first_string(normalized.get("category"), normalized.get("domain"), normalized.get("type"))
    if category:
        normalized["category"] = category
    return normalized


def metadata_value(metadata: dict[str, Any], key: str) -> Any:
    normalized = normalize_metadata(metadata)
    if key in {"category", "domain", "type"}:
        return normalized.get("category")
    return normalized.get(key)


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None
