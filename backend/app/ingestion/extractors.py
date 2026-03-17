from __future__ import annotations

import io
import json
from typing import Any

from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.ingestion.normalizers import flatten_json, normalize_text


SUPPORTED_FILE_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".html": "text/html",
    ".htm": "text/html",
    ".json": "application/json",
}


def extract_text(content: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return _extract_pdf(content)
    if content_type == "text/html":
        return _extract_html(content)
    if content_type == "text/markdown":
        return _extract_markdown(content)
    if content_type == "application/json":
        return _extract_json(content)
    raise ValueError(f"Unsupported content type: {content_type}")


def detect_content_type(filename: str | None, content_type: str | None) -> str:
    if content_type:
        normalized = content_type.split(";")[0].strip().lower()
        if normalized in {"application/pdf", "text/html", "text/markdown", "application/json"}:
            return normalized
    if filename:
        lower_name = filename.lower()
        for suffix, mapped_type in SUPPORTED_FILE_TYPES.items():
            if lower_name.endswith(suffix):
                return mapped_type
    raise ValueError("Unsupported file type.")


def extract_payload_text(payload: dict[str, Any] | list[Any] | str) -> str:
    if isinstance(payload, str):
        return normalize_text(payload)
    return normalize_text(flatten_json(payload))


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    parts = [page.extract_text() or "" for page in reader.pages]
    return normalize_text("\n".join(parts))


def _extract_html(content: bytes) -> str:
    soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body = soup.body or soup
    return normalize_text(body.get_text("\n"))


def _extract_markdown(content: bytes) -> str:
    return normalize_text(content.decode("utf-8", errors="ignore"))


def _extract_json(content: bytes) -> str:
    parsed = json.loads(content.decode("utf-8"))
    return normalize_text(flatten_json(parsed))
