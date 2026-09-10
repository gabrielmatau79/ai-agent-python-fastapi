from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class BaseMemoryProvider(ABC):
    async def start(self) -> None:
        return

    async def close(self) -> None:
        return

    @abstractmethod
    async def get_history(self, session_id: str) -> list[ChatMessage]:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_all(self) -> None:
        raise NotImplementedError
