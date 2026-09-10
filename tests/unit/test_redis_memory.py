from fnmatch import fnmatch

import pytest

from app.core.settings import Settings
from app.memory.providers.redis_memory import RedisMemoryProvider


class FakePipeline:
    def __init__(self, storage: dict[str, list[str]], ttl: dict[str, int]) -> None:
        self.storage = storage
        self.ttl = ttl
        self.key = ""
        self.payload = ""
        self.window = 0

    async def __aenter__(self) -> "FakePipeline":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def rpush(self, key: str, payload: str) -> None:
        self.key = key
        self.payload = payload
        self.storage.setdefault(key, []).append(payload)

    async def ltrim(self, key: str, start: int, end: int) -> None:
        values = self.storage.get(key, [])
        self.storage[key] = values[start : end + 1 if end != -1 else None]

    async def expire(self, key: str, ttl: int) -> None:
        self.ttl[key] = ttl

    async def execute(self) -> None:
        return None


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, list[str]] = {}
        self.ttl: dict[str, int] = {}

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        values = self.storage.get(key, [])
        return values[start : end + 1 if end != -1 else None]

    def pipeline(self, transaction: bool = True) -> FakePipeline:
        _ = transaction
        return FakePipeline(self.storage, self.ttl)

    async def delete(self, key: str) -> None:
        self.storage.pop(key, None)

    async def scan_iter(self, match: str, count: int):
        for key in list(self.storage):
            if fnmatch(key, match):
                yield key


@pytest.mark.asyncio
async def test_redis_memory_uses_ttl_and_window() -> None:
    fake_redis = FakeRedis()
    settings = Settings(agent_memory_window=2, memory_ttl_seconds=60)
    provider = RedisMemoryProvider(settings, client=fake_redis)  # type: ignore[arg-type]
    await provider.add_message("s1", "user", "one")
    await provider.add_message("s1", "assistant", "two")
    await provider.add_message("s1", "user", "three")
    history = await provider.get_history("s1")
    assert [item.content for item in history] == ["two", "three"]
    assert fake_redis.ttl["chat:history:s1"] == 60


async def test_clear_all_removes_histories_but_preserves_other_redis_data() -> None:
    client = FakeRedis()
    provider = RedisMemoryProvider(Settings(), client=client)  # type: ignore[arg-type]
    await provider.add_message("one", "user", "old")
    await provider.add_message("two", "assistant", "old")
    client.storage["rag:documents"] = ["keep"]
    await provider.clear_all()
    assert client.storage == {"rag:documents": ["keep"]}
