from __future__ import annotations

import hashlib
import math
from typing import Protocol

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.core.config import Settings
from app.providers.errors import ProviderRequestError


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class MockEmbeddingProvider:
    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when embedding_provider=openai.")
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.request_timeout_seconds,
        )
        self._model = settings.embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(model=self._model, input=texts)
        except APITimeoutError as exc:
            raise ProviderRequestError(
                stage="embedding",
                reason="timeout",
                message="The embedding request timed out. Try a shorter query or retry shortly.",
            ) from exc
        except APIConnectionError as exc:
            raise ProviderRequestError(
                stage="embedding",
                reason="connection",
                message="The embedding provider could not be reached. Check network connectivity and upstream availability.",
            ) from exc
        except APIStatusError as exc:
            raise ProviderRequestError(
                stage="embedding",
                reason="status",
                message=_status_message("embedding", exc.status_code),
            ) from exc
        return [item.embedding for item in response.data]


def _status_message(stage: str, status_code: int | None) -> str:
    if status_code == 401:
        return f"The {stage} provider rejected the API key."
    if status_code == 403:
        return f"The configured account does not have access to the {stage} model."
    if status_code == 429:
        return f"The {stage} provider rate limit was reached. Retry shortly."
    if status_code == 400:
        return f"The {stage} request was rejected by the provider. Check the request size and payload."
    return f"The {stage} provider returned an unexpected status error."
