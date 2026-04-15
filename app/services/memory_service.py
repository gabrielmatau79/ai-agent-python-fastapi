from __future__ import annotations

from app.memory.base import BaseMemoryProvider, ChatMessage


class MemoryService:
    def __init__(self, provider: BaseMemoryProvider) -> None:
        self._provider = provider

    async def start(self) -> None:
        await self._provider.start()

    async def close(self) -> None:
        await self._provider.close()

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        return await self._provider.get_history(session_id)

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        await self._provider.add_message(session_id, role, content)

    async def clear(self, session_id: str) -> None:
        await self._provider.clear(session_id)
