from __future__ import annotations

import unittest

from app.core.config import Settings
from app.generation.language import build_no_context_answer
from app.generation.prompts import ACTIVITY_CATALOG_RULES, build_context
from app.generation.providers import MockGenerationProvider
from app.generation.service import GenerationService


class GenerationLanguageTests(unittest.TestCase):
    def test_prompt_instructs_english_output_for_english_query(self) -> None:
        prompt = build_context(
            "Which activities are available in Tromso?",
            [],
            max_characters=6000,
            mode="activity_catalog",
        )
        self.assertIn(
            "Write the visible answer in English, matching the user's question language.",
            prompt,
        )

    def test_prompt_instructs_italian_output_for_italian_query(self) -> None:
        prompt = build_context(
            "Quali attività sono disponibili a Tromsø?",
            [],
            max_characters=6000,
            mode="activity_catalog",
        )
        self.assertIn(
            "Write the visible answer in Italian, matching the user's question language.",
            prompt,
        )

    def test_no_context_answer_follows_english_query_language(self) -> None:
        service = GenerationService(Settings(), MockGenerationProvider())
        payload = service.generate_answer("What activities are available in Alta?", [])
        self.assertEqual(
            payload["answer"],
            "## Answer\n\nI could not find enough indexed content to answer that question.",
        )

    def test_no_context_answer_defaults_to_italian_when_query_is_italian(self) -> None:
        self.assertEqual(
            build_no_context_answer("Quali attività sono disponibili ad Alta?"),
            "## Risposta\n\nNon ho trovato abbastanza contenuto indicizzato per rispondere a questa domanda.",
        )

    def test_no_context_answer_defaults_to_english_for_ambiguous_query(self) -> None:
        self.assertEqual(
            build_no_context_answer("VAT?"),
            "## Answer\n\nI could not find enough indexed content to answer that question.",
        )

    def test_activity_catalog_rules_do_not_hardcode_italian_placeholders(self) -> None:
        self.assertNotIn("Nome attività", ACTIVITY_CATALOG_RULES)
        self.assertNotIn("una frase breve", ACTIVITY_CATALOG_RULES)
        self.assertNotIn("Non specificato", ACTIVITY_CATALOG_RULES)

    def test_mock_activity_catalog_answer_uses_english_defaults_for_english_query(self) -> None:
        provider = MockGenerationProvider()
        payload = provider.generate("Question: What activities are available?\n[12345678-1234-1234-1234-123456789012] document=doc score=0.99\nAlta husky safari", mode="activity_catalog")
        self.assertIn("## Extracted activity", payload["answer"])
        self.assertIn("- Location: Not specified", payload["answer"])


if __name__ == "__main__":
    unittest.main()
