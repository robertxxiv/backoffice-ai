from __future__ import annotations

import json
from typing import Any, Protocol

from openai import OpenAI

from app.core.config import Settings
from app.generation.formatting import GenerationMode


class GenerationProvider(Protocol):
    def generate(self, prompt: str, mode: GenerationMode = "standard") -> dict[str, object]:
        ...


class MockGenerationProvider:
    def generate(self, prompt: str, mode: GenerationMode = "standard") -> dict[str, object]:
        citations = [line[1:37] for line in prompt.splitlines() if line.startswith("[")][:3]
        excerpts = _extract_excerpts(prompt)
        answer = "## Answer\n\nNo indexed context was found."
        machine_output: dict[str, Any] | None = None
        if citations:
            if mode == "activity_catalog":
                machine_output = {
                    "activities": [
                        {
                            "activity": excerpts[0] if excerpts else "Non specificato",
                            "location": None,
                            "duration": None,
                            "environment": None,
                            "requirements": {"age": None, "license": None, "notes": None},
                        }
                    ]
                }
                answer = (
                    "# HUMAN OUTPUT\n\n"
                    "## Attività estratta\n\n"
                    "### Overview\n"
                    "Sintesi dell'attività trovata nel contenuto indicizzato.\n\n"
                    "### Details\n"
                    "- Location: Non specificato\n"
                    "- Duration: Non specificato\n"
                    "- Environment: Non specificato\n\n"
                    "### Requirements\n"
                    "- Age: Non specificato\n"
                    "- License: Non specificato\n"
                    "- Notes: Non specificato\n\n"
                    "### Experience\n"
                    f"- {excerpts[0] if excerpts else 'Contenuto disponibile nel catalogo.'}"
                )
            else:
                bullets = "\n".join(f"- {excerpt}" for excerpt in excerpts) or "- No indexed context was found."
                answer = f"## Answer\n\n{bullets}"
        return {"answer": answer, "citations": citations, "machine_output": machine_output}


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

    def generate(self, prompt: str, mode: GenerationMode = "standard") -> dict[str, object]:
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "citations": {"type": "array", "items": {"type": "string"}},
                "machine_output": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "properties": {
                                "activities": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "activity": {"type": ["string", "null"]},
                                            "location": {"type": ["string", "null"]},
                                            "duration": {"type": ["string", "null"]},
                                            "environment": {"type": ["string", "null"]},
                                            "requirements": {
                                                "type": "object",
                                                "properties": {
                                                    "age": {"type": ["string", "null"]},
                                                    "license": {"type": ["string", "null"]},
                                                    "notes": {"type": ["string", "null"]},
                                                },
                                                "required": ["age", "license", "notes"],
                                                "additionalProperties": False,
                                            },
                                        },
                                        "required": [
                                            "activity",
                                            "location",
                                            "duration",
                                            "environment",
                                            "requirements",
                                        ],
                                        "additionalProperties": False,
                                    },
                                }
                            },
                            "required": ["activities"],
                            "additionalProperties": False,
                        },
                    ]
                },
            },
            "required": ["answer", "citations", "machine_output"],
            "additionalProperties": False,
        }
        response = self._client.responses.create(
            model=self._model,
            instructions=(
                "Answer only from the provided context. "
                "Return valid JSON matching the schema. "
                "Write visible output only in the `answer` field as Markdown. "
                "Never expose UUIDs, chunk ids, or internal ids in the visible answer. "
                "Use the `citations` array for source references. "
                "Use `machine_output` for structured extraction data when the prompt requests it."
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
