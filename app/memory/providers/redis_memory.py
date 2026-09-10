from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.exceptions import ExternalServiceError
from app.core.settings import Settings
from app.memory.base import BaseMemoryProvider, ChatMessage


class RedisMemoryProvider(BaseMemoryProvider):
    def __init__(self, settings: Settings, client: Redis | None = None) -> None:
        self._settings = settings
        self._client: Any = client or Redis.from_url(settings.redis_url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"chat:history:{session_id}"

    async def start(self) -> None:
        try:
            await self._client.ping()
        except RedisError as exc:
            raise ExternalServiceError(f"Redis memory startup failed: {exc}") from exc

    async def close(self) -> None:
        await self._client.aclose()

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        try:
            values = await self._client.lrange(self._key(session_id), 0, -1)
            return [ChatMessage.model_validate_json(value) for value in values]
        except RedisError as exc:
            raise ExternalServiceError(f"Redis memory read failed: {exc}") from exc

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        payload = ChatMessage(role=role, content=content).model_dump_json()
        key = self._key(session_id)
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                await pipe.rpush(key, payload)
                await pipe.ltrim(key, -self._settings.agent_memory_window, -1)
                await pipe.expire(key, self._settings.memory_ttl_seconds)
                await pipe.execute()
        except RedisError as exc:
            raise ExternalServiceError(f"Redis memory write failed: {exc}") from exc

    async def clear(self, session_id: str) -> None:
        try:
            await self._client.delete(self._key(session_id))
        except RedisError as exc:
            raise ExternalServiceError(f"Redis memory clear failed: {exc}") from exc

    async def clear_all(self) -> None:
        try:
            async for key in self._client.scan_iter(match="chat:history:*", count=100):
                await self._client.delete(key)
        except RedisError as exc:
            raise ExternalServiceError(f"Redis memory clear failed: {exc}") from exc
