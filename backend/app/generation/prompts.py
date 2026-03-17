from __future__ import annotations

from app.retrieval.schemas import RetrievedChunk

SYSTEM_PROMPT = """
You are a grounded decision support assistant.
Answer only from the provided context.
If the context is insufficient, say so explicitly.
Use inline citations in the answer with chunk ids like [chunk-id].
""".strip()


def build_context(query: str, chunks: list[RetrievedChunk], max_characters: int) -> str:
    parts = [f"Question: {query}", "", "Context:"]
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
