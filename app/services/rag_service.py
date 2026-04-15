from __future__ import annotations

from app.rag.base import BaseRagProvider
from app.rag.models import RetrievalResult


class RagService:
    def __init__(self, provider: BaseRagProvider) -> None:
        self._provider = provider

    async def start(self) -> None:
        await self._provider.start()

    async def close(self) -> None:
        await self._provider.close()

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[RetrievalResult]:
        return await self._provider.retrieve(query, top_k=top_k)

    async def reindex(self) -> tuple[int, int]:
        return await self._provider.reindex()
