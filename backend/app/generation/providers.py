from __future__ import annotations

import json
from typing import Protocol

from openai import OpenAI

from app.core.config import Settings


class GenerationProvider(Protocol):
    def generate(self, prompt: str) -> dict[str, object]:
        ...


class MockGenerationProvider:
    def generate(self, prompt: str) -> dict[str, object]:
        citations = [line[1:37] for line in prompt.splitlines() if line.startswith("[")][:3]
        excerpts = _extract_excerpts(prompt)
        answer = "No indexed context was found."
        if citations:
            details = " ".join(
                f"{excerpt} [{citation}]"
                for excerpt, citation in zip(excerpts, citations, strict=False)
            )
            answer = f"Based on the indexed context: {details}".strip()
        return {"answer": answer, "citations": citations}


class OpenAIGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when generation_provider=openai.")
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.request_timeout_seconds,
        )
        self._model = settings.generation_model

    def generate(self, prompt: str) -> dict[str, object]:
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "citations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["answer", "citations"],
            "additionalProperties": False,
        }
        response = self._client.responses.create(
            model=self._model,
            instructions=(
                "Answer only from the provided context. "
                "If context is insufficient, say so. "
                "Use inline citations such as [chunk-id]."
            ),
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "rag_answer",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return json.loads(response.output_text)


def _extract_excerpts(prompt: str) -> list[str]:
    lines = [line.strip() for line in prompt.splitlines() if line and not line.startswith("Question:")]
    excerpts = [line[:180] for line in lines if not line.startswith("[") and line != "Context:"]
    return excerpts[:3]
