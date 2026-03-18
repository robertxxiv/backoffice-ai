from __future__ import annotations

import unittest

from app.core.config import Settings
from app.generation.guardrails import strip_external_lookup_offers
from app.generation.service import GenerationService


class GenerationGuardrailTests(unittest.TestCase):
    def test_strip_external_lookup_offer_from_answer(self) -> None:
        answer = (
            "## Answer\n\n"
            "I do not have enough indexed context to answer that question.\n\n"
            "If you'd like, I can look up and provide a list of restaurants in Tromso from external sources — shall I search the web for that?"
        )
        cleaned = strip_external_lookup_offers(answer)
        self.assertEqual(
            cleaned,
            "## Answer\n\nI do not have enough indexed context to answer that question.",
        )

    def test_generation_service_removes_external_lookup_offer(self) -> None:
        class StubProvider:
            def generate(self, prompt: str, mode: str = "standard") -> dict[str, object]:
                return {
                    "answer": (
                        "## Answer\n\n"
                        "I do not have enough indexed context to answer that question.\n\n"
                        "If you'd like, I can search the web for that."
                    ),
                    "citations": [],
                    "machine_output": None,
                }

        service = GenerationService(Settings(), StubProvider())
        payload = service.generate_answer(
            "What kind of restaurants are in Tromso?",
            [
                type(
                    "Chunk",
                    (),
                    {
                        "document_id": "doc-1",
                        "document_ref": "catalog",
                        "chunk_id": "chunk-1",
                        "score": 0.3,
                        "content": "Winter activities in Tromso.",
                        "metadata": {},
                    },
                )()
            ],
        )
        self.assertEqual(
            payload["answer"],
            "## Answer\n\nI do not have enough indexed context to answer that question.",
        )


if __name__ == "__main__":
    unittest.main()
