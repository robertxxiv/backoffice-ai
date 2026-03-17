from __future__ import annotations

from app.chunking.schemas import ChunkCandidate, ChunkRequest
from app.chunking.tokenizer import decode_tokens, encode_text


def build_chunks(document_id: str, content: str, source_ref: str, request: ChunkRequest) -> list[ChunkCandidate]:
    token_ids = encode_text(content)
    if not token_ids:
        return []
    step = request.chunk_size - request.overlap_tokens
    candidates: list[ChunkCandidate] = []
    for index, start in enumerate(range(0, len(token_ids), step)):
        window = token_ids[start : start + request.chunk_size]
        chunk_text = decode_tokens(window)
        if not chunk_text.strip():
            continue
        candidates.append(
            ChunkCandidate(
                chunk_index=index,
                content=chunk_text,
                token_count=len(window),
                strategy=request.strategy,
                section=None,
                metadata={
                    "document_id": document_id,
                    "source_ref": source_ref,
                    "chunk_index": index,
                    "strategy": request.strategy,
                    "chunk_size": request.chunk_size,
                    "overlap_tokens": request.overlap_tokens,
                },
            )
        )
        if start + request.chunk_size >= len(token_ids):
            break
    return candidates
