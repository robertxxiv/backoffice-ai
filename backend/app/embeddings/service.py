from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Chunk, Document, Embedding
from app.embeddings.providers import EmbeddingProvider, MockEmbeddingProvider, OpenAIEmbeddingProvider


class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider, model_name: str) -> None:
        self._provider = provider
        self._model_name = model_name

    def embed_document_chunks(self, document_id: str, session: Session) -> int:
        document = session.get(Document, document_id)
        if document is None:
            raise LookupError(f"Document '{document_id}' was not found.")
        chunks = list(session.scalars(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)))
        if not chunks:
            raise ValueError("Document must be chunked before embeddings can be generated.")
        vectors = self._provider.embed_texts([chunk.content for chunk in chunks])
        chunk_ids = [chunk.id for chunk in chunks]
        session.execute(delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids)))
        embeddings = [
            Embedding(chunk_id=chunk.id, model=self._model_name, vector=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        session.add_all(embeddings)
        document.status = "indexed"
        session.commit()
        return len(embeddings)


def build_embedding_service(settings: Settings) -> EmbeddingService:
    if settings.embedding_provider == "openai":
        provider: EmbeddingProvider = OpenAIEmbeddingProvider(settings)
    else:
        provider = MockEmbeddingProvider(settings.embedding_dimensions)
    return EmbeddingService(provider=provider, model_name=settings.embedding_model)
