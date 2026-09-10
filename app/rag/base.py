from __future__ import annotations

from abc import ABC, abstractmethod

from app.rag.models import IndexedChunk, RetrievalResult


class BaseRagProvider(ABC):
    async def start(self) -> None:
        return

    async def close(self) -> None:
        return

    @abstractmethod
    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[RetrievalResult]:
        raise NotImplementedError

    @abstractmethod
    async def reindex(self) -> tuple[int, int]:
        raise NotImplementedError

    @abstractmethod
    async def add_chunks(self, chunks: list[IndexedChunk]) -> None:
        raise NotImplementedError
