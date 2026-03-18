from __future__ import annotations

from app.generation.formatting import GenerationMode
from app.generation.language import build_language_instruction
from app.retrieval.schemas import RetrievedChunk

STANDARD_RULES = """
Output requirements:
- Write clean human-readable Markdown in the `answer` field.
- Use headings and bullets when they help readability.
- Do not include UUIDs, chunk ids, or internal ids in the visible answer.
- Keep citations only in the `citations` array.
- Set `machine_output` to null unless structured extraction is clearly required.
- If the indexed context is insufficient, say so briefly and stop.
- Do not offer to search the web, browse external sources, look things up, or continue outside the indexed corpus.
""".strip()

ACTIVITY_CATALOG_RULES = """
Role: data formatter for enterprise RAG output.

Task:
- Transform retrieved catalog or brochure content into clean, structured, consistent Markdown in the same language as the user's question.
- Remove duplicates, UUIDs, internal ids, and irrelevant phrases.
- Never compress multiple attributes into one line.

Human output rules for the `answer` field:
- Always write Markdown.
- Always use headings and sections.
- If multiple activities are present, create one section per activity.
- Use this schema for each activity when information is available:
  ## <Activity name>
  ### Overview
  <one short sentence>
  ### Details
  - Location:
  - Duration:
  - Environment:
  ### Requirements
  - Age:
  - License:
  - Notes:
  ### Experience
  - <bullet item>
- If a field is missing, write a clear equivalent of `Not specified` in the user's language.
- Translate mixed content to the same language as the user's question.
- Normalize durations, participant references, and age notes into a clean human-readable form in the user's language.
- Never include UUIDs or chunk ids in the visible answer.
- If the indexed context is insufficient, say so briefly and stop.
- Do not offer to search the web, browse external sources, look things up, or continue outside the indexed corpus.

Machine output rules for the `machine_output` field:
- Return an object with an `activities` array.
- Each item must be:
  {
    "activity": "",
    "location": "",
    "duration": "",
    "environment": "",
    "requirements": {
      "age": "",
      "license": "",
      "notes": ""
    }
  }
- Use null for missing fields.
- If no activity can be extracted, return {"activities": []}.
""".strip()


def build_context(
    query: str,
    chunks: list[RetrievedChunk],
    max_characters: int,
    mode: GenerationMode,
) -> str:
    parts = [f"Question: {query}", "", f"Response mode: {mode}", ""]
    parts.append("Instructions:")
    parts.append(build_language_instruction(query))
    parts.append(ACTIVITY_CATALOG_RULES if mode == "activity_catalog" else STANDARD_RULES)
    parts.extend(["", "Context:"])
    total = 0
    for chunk in chunks:
        block = (
            f"[{chunk.chunk_id}] document={chunk.document_ref} score={chunk.score:.4f}\n"
            f"{chunk.content}\n"
        )
        if total + len(block) > max_characters:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)
