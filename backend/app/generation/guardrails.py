from __future__ import annotations

import re

EXTERNAL_LOOKUP_PATTERNS = [
    r"(?i)\bsearch the web\b",
    r"(?i)\bsearch online\b",
    r"(?i)\bsearch externally\b",
    r"(?i)\bexternal sources?\b",
    r"(?i)\bbrowse the web\b",
    r"(?i)\blook up\b",
    r"(?i)\bshall i search\b",
    r"(?i)\bi can search\b",
    r"(?i)\bi can look up\b",
    r"(?i)\bposso cercare sul web\b",
    r"(?i)\bfonti esterne\b",
    r"(?i)\bvuoi che cerchi\b",
]


def strip_external_lookup_offers(answer: str) -> str:
    lines = [line.rstrip() for line in answer.splitlines()]
    filtered_lines = [line for line in lines if not _contains_external_lookup_offer(line)]
    cleaned = "\n".join(filtered_lines).strip()
    return cleaned or answer.strip()


def _contains_external_lookup_offer(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(re.search(pattern, normalized) for pattern in EXTERNAL_LOOKUP_PATTERNS)
