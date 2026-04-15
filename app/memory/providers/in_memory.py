from __future__ import annotations

from collections import defaultdict

from app.core.settings import Settings
from app.memory.base import BaseMemoryProvider, ChatMessage


class InMemoryMemoryProvider(BaseMemoryProvider):
    def __init__(self, settings: Settings) -> None:
        self._window = settings.agent_memory_window
        self._store: dict[str, list[ChatMessage]] = defaultdict(list)

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        return list(self._store.get(session_id, []))

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        history = self._store.setdefault(session_id, [])
        history.append(ChatMessage(role=role, content=content))
        if len(history) > self._window:
            del history[: -self._window]

    async def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)
