from __future__ import annotations

import json
import re
from typing import Any


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
            continue
        if current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return "\n\n".join(blocks)


def flatten_json(value: Any) -> str:
    lines: list[str] = []
    _flatten(value, prefix="", lines=lines)
    return "\n".join(lines) if lines else json.dumps(value, ensure_ascii=True)


def _flatten(value: Any, prefix: str, lines: list[str]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            _flatten(value[key], next_prefix, lines)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            next_prefix = f"{prefix}[{index}]"
            _flatten(item, next_prefix, lines)
        return
    rendered = json.dumps(value, ensure_ascii=True) if value is not None else "null"
    lines.append(f"{prefix}: {rendered}")
