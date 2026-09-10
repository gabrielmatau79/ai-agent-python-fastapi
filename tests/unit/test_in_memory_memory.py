import pytest

from app.core.settings import Settings
from app.memory.providers.in_memory import InMemoryMemoryProvider
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_in_memory_memory_respects_window() -> None:
    provider = InMemoryMemoryProvider(Settings(agent_memory_window=2))
    await provider.add_message("s1", "user", "one")
    await provider.add_message("s1", "assistant", "two")
    await provider.add_message("s1", "user", "three")
    history = await provider.get_history("s1")
    assert [item.content for item in history] == ["two", "three"]


async def test_replaced_memory_rejects_late_turns() -> None:
    service = MemoryService(InMemoryMemoryProvider(Settings()))
    revision = service.revision
    await service.close()
    await service.add_turn("one", "old question", "old answer", revision=revision)
    assert await service.get_history("one") == []
