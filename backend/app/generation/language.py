from __future__ import annotations

import re

ITALIAN_MARKERS = {
    "che",
    "chi",
    "come",
    "cosa",
    "dove",
    "grazie",
    "il",
    "la",
    "per",
    "quale",
    "quali",
    "quanto",
    "sono",
}

ENGLISH_MARKERS = {
    "and",
    "are",
    "available",
    "how",
    "is",
    "the",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
}


def detect_query_language(query: str) -> str:
    tokens = set(re.findall(r"[A-Za-zÀ-ÿ']+", query.lower()))
    italian_score = len(tokens & ITALIAN_MARKERS)
    english_score = len(tokens & ENGLISH_MARKERS)
    if italian_score > english_score:
        return "it"
    if english_score > italian_score:
        return "en"
    return "same"


def build_language_instruction(query: str) -> str:
    language = detect_query_language(query)
    if language == "it":
        return "Write the visible answer in Italian, matching the user's question language."
    if language == "en":
        return "Write the visible answer in English, matching the user's question language."
    return "Write the visible answer in the same language as the user's question."


def build_no_context_answer(query: str) -> str:
    language = detect_query_language(query)
    if language != "it":
        return "## Answer\n\nI could not find enough indexed content to answer that question."
    return "## Risposta\n\nNon ho trovato abbastanza contenuto indicizzato per rispondere a questa domanda."


def missing_value_label(query: str) -> str:
    return "Not specified" if detect_query_language(query) != "it" else "Non specificato"


def extracted_activity_overview(query: str) -> str:
    if detect_query_language(query) == "it":
        return "Sintesi dell'attività trovata nel contenuto indicizzato."
    return "Summary of the activity found in the indexed content."


def catalog_content_label(query: str) -> str:
    if detect_query_language(query) == "it":
        return "Contenuto disponibile nel catalogo."
    return "Content available in the catalog."
