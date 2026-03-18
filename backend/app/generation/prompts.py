from __future__ import annotations

from app.generation.formatting import GenerationMode
from app.retrieval.schemas import RetrievedChunk

STANDARD_RULES = """
Output requirements:
- Write clean human-readable Markdown in the `answer` field.
- Use headings and bullets when they help readability.
- Do not include UUIDs, chunk ids, or internal ids in the visible answer.
- Keep citations only in the `citations` array.
- Set `machine_output` to null unless structured extraction is clearly required.
""".strip()

ACTIVITY_CATALOG_RULES = """
Role: data formatter for enterprise RAG output.

Task:
- Transform retrieved catalog or brochure content into clean, structured, consistent Markdown in Italian.
- Remove duplicates, UUIDs, internal ids, and irrelevant phrases.
- Never compress multiple attributes into one line.

Human output rules for the `answer` field:
- Always write Markdown.
- Always use headings and sections.
- If multiple activities are present, create one section per activity.
- Use this schema for each activity when information is available:
  ## <Nome attività>
  ### Overview
  <una frase breve>
  ### Details
  - Location:
  - Duration:
  - Environment:
  ### Requirements
  - Age:
  - License:
  - Notes:
  ### Experience
  - <punto>
- If a field is missing, write `Non specificato`.
- Translate mixed content to Italian.
- Normalize durations like `4 ore`, passenger references like `partecipanti`, and age notes like `Età minima: 12 anni`.
- Never include UUIDs or chunk ids in the visible answer.

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
