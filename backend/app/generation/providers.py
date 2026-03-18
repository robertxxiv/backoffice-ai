from __future__ import annotations

import json
from typing import Any, Protocol

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.core.config import Settings
from app.generation.formatting import GenerationMode
from app.generation.language import (
    catalog_content_label,
    extracted_activity_overview,
    missing_value_label,
)
from app.providers.errors import ProviderRequestError


class GenerationProvider(Protocol):
    def generate(self, prompt: str, mode: GenerationMode = "standard") -> dict[str, object]:
        ...


class MockGenerationProvider:
    def generate(self, prompt: str, mode: GenerationMode = "standard") -> dict[str, object]:
        query = _extract_question(prompt)
        missing = missing_value_label(query)
        citations = [line[1:37] for line in prompt.splitlines() if line.startswith("[")][:3]
        excerpts = _extract_excerpts(prompt)
        answer = "## Answer\n\nNo indexed context was found."
        machine_output: dict[str, Any] | None = None
        if citations:
            if mode == "activity_catalog":
                machine_output = {
                    "activities": [
                        {
                            "activity": excerpts[0] if excerpts else missing,
                            "location": None,
                            "duration": None,
                            "environment": None,
                            "requirements": {"age": None, "license": None, "notes": None},
                        }
                    ]
                }
                answer = (
                    "# HUMAN OUTPUT\n\n"
                    "## Extracted activity\n\n"
                    "### Overview\n"
                    f"{extracted_activity_overview(query)}\n\n"
                    "### Details\n"
                    f"- Location: {missing}\n"
                    f"- Duration: {missing}\n"
                    f"- Environment: {missing}\n\n"
                    "### Requirements\n"
                    f"- Age: {missing}\n"
                    f"- License: {missing}\n"
                    f"- Notes: {missing}\n\n"
                    "### Experience\n"
                    f"- {excerpts[0] if excerpts else catalog_content_label(query)}"
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
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=(
                    "Answer only from the provided context. "
                    "Return valid JSON matching the schema. "
                    "Write visible output only in the `answer` field as Markdown. "
                    "Write the visible answer in the same language as the user's question. "
                    "If the indexed context is insufficient, say so briefly and stop. "
                    "Do not offer to search the web, browse external sources, or continue outside the indexed corpus. "
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
        except APITimeoutError as exc:
            raise ProviderRequestError(
                stage="generation",
                reason="timeout",
                message="The answer generation request timed out. Try a shorter question or retry shortly.",
            ) from exc
        except APIConnectionError as exc:
            raise ProviderRequestError(
                stage="generation",
                reason="connection",
                message="The answer generation provider could not be reached. Check network connectivity and upstream availability.",
            ) from exc
        except APIStatusError as exc:
            raise ProviderRequestError(
                stage="generation",
                reason="status",
                message=_status_message("generation", exc.status_code),
            ) from exc
        return json.loads(response.output_text)


def _extract_excerpts(prompt: str) -> list[str]:
    lines = [line.strip() for line in prompt.splitlines() if line and not line.startswith("Question:")]
    excerpts = [line[:180] for line in lines if not line.startswith("[") and line != "Context:"]
    return excerpts[:3]


def _extract_question(prompt: str) -> str:
    for line in prompt.splitlines():
        if line.startswith("Question: "):
            return line.removeprefix("Question: ").strip()
    return ""


def _status_message(stage: str, status_code: int | None) -> str:
    if status_code == 401:
        return f"The {stage} provider rejected the API key."
    if status_code == 403:
        return f"The configured account does not have access to the {stage} model."
    if status_code == 429:
        return f"The {stage} provider rate limit was reached. Retry shortly."
    if status_code == 400:
        return f"The {stage} request was rejected by the provider. Check the request size and prompt constraints."
    return f"The {stage} provider returned an unexpected status error."
