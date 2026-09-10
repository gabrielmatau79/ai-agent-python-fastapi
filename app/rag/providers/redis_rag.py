from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.exceptions import ExternalServiceError
from app.core.settings import Settings
from app.rag.base import BaseRagProvider
from app.rag.ingestion.chunking import chunk_text
from app.rag.ingestion.embeddings import EmbeddingService
from app.rag.ingestion.loaders import load_documents
from app.rag.models import IndexedChunk, RetrievalResult


class RedisRagProvider(BaseRagProvider):
    def __init__(
        self, settings: Settings, embedding_service: EmbeddingService, client: Redis | None = None
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._client: Any = client or Redis.from_url(settings.redis_url, decode_responses=True)

    def _index_key(self) -> str:
        return f"rag:index:{self._settings.vector_index_name}"

    async def start(self) -> None:
        try:
            await self._client.ping()
        except RedisError as exc:
            raise ExternalServiceError(f"Redis RAG startup failed: {exc}") from exc
        await self.reindex()

    async def close(self) -> None:
        await self._client.aclose()

    async def reindex(self) -> tuple[int, int]:
        documents = load_documents(self._settings.rag_docs_path)
        chunks: list[IndexedChunk] = []
        for document in documents:
            for index, chunk in enumerate(
                chunk_text(
                    document.content,
                    chunk_size=self._settings.rag_chunk_size,
                    chunk_overlap=self._settings.rag_chunk_overlap,
                )
            ):
                chunks.append(
                    IndexedChunk(
                        id=f"{document.source}:{index}",
                        source=document.source,
                        content=chunk,
                        embedding=await self._embedding_service.embed(chunk),
                    )
                )
        try:
            await self._client.delete(self._index_key())
            if chunks:
                mapping = {chunk.id: chunk.model_dump_json() for chunk in chunks}
                await self._client.hset(self._index_key(), mapping=mapping)
        except RedisError as exc:
            raise ExternalServiceError(f"Redis RAG reindex failed: {exc}") from exc
        return len(documents), len(chunks)

    async def add_chunks(self, chunks: list[IndexedChunk]) -> None:
        try:
            if chunks:
                await self._client.hset(
                    self._index_key(),
                    mapping={chunk.id: chunk.model_dump_json() for chunk in chunks},
                )
        except RedisError as exc:
            raise ExternalServiceError(f"Redis RAG add chunks failed: {exc}") from exc

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[RetrievalResult]:
        try:
            raw = await self._client.hvals(self._index_key())
        except RedisError as exc:
            raise ExternalServiceError(f"Redis RAG read failed: {exc}") from exc
        chunks = [IndexedChunk.model_validate_json(value) for value in raw]
        query_embedding = await self._embedding_service.embed(query)
        ranked = sorted(
            (
                RetrievalResult(
                    source=chunk.source,
                    content=chunk.content,
                    score=_cosine_similarity(query_embedding, chunk.embedding),
                )
                for chunk in chunks
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
