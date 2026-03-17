from __future__ import annotations

from app.core.config import Settings
from app.generation.prompts import build_context
from app.generation.providers import GenerationProvider, MockGenerationProvider, OpenAIGenerationProvider
from app.retrieval.schemas import RetrievedChunk


class GenerationService:
    def __init__(self, settings: Settings, provider: GenerationProvider) -> None:
        self._settings = settings
        self._provider = provider

    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> dict[str, object]:
        prompt = build_context(query, chunks, self._settings.context_character_limit)
        if not chunks:
            return {"answer": "I could not find enough indexed context to answer that question.", "citations": []}
        return self._provider.generate(prompt)


def build_generation_service(settings: Settings) -> GenerationService:
    if settings.generation_provider == "openai":
        provider: GenerationProvider = OpenAIGenerationProvider(settings)
    else:
        provider = MockGenerationProvider()
    return GenerationService(settings=settings, provider=provider)
