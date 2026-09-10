from __future__ import annotations

from app.core.settings import Settings
from app.rag.base import BaseRagProvider
from app.rag.ingestion.chunking import chunk_text
from app.rag.ingestion.embeddings import EmbeddingService
from app.rag.ingestion.loaders import load_documents
from app.rag.models import IndexedChunk, RetrievalResult


class InMemoryRagProvider(BaseRagProvider):
    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._chunks: list[IndexedChunk] = []

    async def start(self) -> None:
        await self.reindex()

    async def reindex(self) -> tuple[int, int]:
        self._chunks.clear()
        documents = load_documents(self._settings.rag_docs_path)
        generated_chunks: list[IndexedChunk] = []
        for document in documents:
            for index, chunk in enumerate(
                chunk_text(
                    document.content,
                    chunk_size=self._settings.rag_chunk_size,
                    chunk_overlap=self._settings.rag_chunk_overlap,
                )
            ):
                generated_chunks.append(
                    IndexedChunk(
                        id=f"{document.source}:{index}",
                        source=document.source,
                        content=chunk,
                        embedding=await self._embedding_service.embed(chunk),
                    )
                )
        self._chunks.extend(generated_chunks)
        return len(documents), len(generated_chunks)

    async def add_chunks(self, chunks: list[IndexedChunk]) -> None:
        self._chunks.extend(chunks)

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[RetrievalResult]:
        query_embedding = await self._embedding_service.embed(query)
        ranked = sorted(
            (
                RetrievalResult(
                    source=chunk.source,
                    content=chunk.content,
                    score=_cosine_similarity(query_embedding, chunk.embedding),
                )
                for chunk in self._chunks
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        return ranked[: top_k or self._settings.rag_top_k]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot_product = sum(float(a * b) for a, b in zip(left, right, strict=False))
    return float(dot_product / (left_norm * right_norm))
