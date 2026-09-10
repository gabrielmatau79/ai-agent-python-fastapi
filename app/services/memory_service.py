from __future__ import annotations

import asyncio

from app.memory.base import BaseMemoryProvider, ChatMessage


class MemoryService:
    def __init__(self, provider: BaseMemoryProvider) -> None:
        self._provider = provider
        self._revision = 0
        self._write_lock = asyncio.Lock()

    @property
    def revision(self) -> int:
        return self._revision

    async def start(self) -> None:
        await self._provider.start()

    async def close(self) -> None:
        async with self._write_lock:
            self._revision += 1
            await self._provider.close()

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        return await self._provider.get_history(session_id)

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        async with self._write_lock:
            await self._provider.add_message(session_id, role, content)

    async def add_turn(
        self, session_id: str, user_input: str, answer: str, *, revision: int
    ) -> None:
        async with self._write_lock:
            # A response generated using old instructions must not restore cleared history.
            if revision != self._revision:
                return
            await self._provider.add_message(session_id, "user", user_input)
            await self._provider.add_message(session_id, "assistant", answer)

    async def clear_all(self) -> None:
        async with self._write_lock:
            await self._provider.clear_all()
            self._revision += 1

    async def clear(self, session_id: str) -> None:
        await self._provider.clear(session_id)
