from typing import Any

import pytest
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from app.core.settings import Settings
from app.llm.base import BaseLlmProvider
from app.services.llm_service import LlmService


class FakeProvider(BaseLlmProvider):
    supports_tools = False

    def __init__(self) -> None:
        self.closed = False

    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        tools: list[BaseTool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return "ok"

    async def close(self) -> None:
        self.closed = True


class FakeToolsService:
    def __init__(self) -> None:
        self.closed = False

    def get_tools(self) -> list[BaseTool]:
        return []

    async def close(self) -> None:
        self.closed = True


class FakeMcpClientService:
    def __init__(self) -> None:
        self.closed = False

    async def load_tools(self) -> list[BaseTool]:
        return []

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_llm_service_close_only_closes_its_own_provider() -> None:
    settings = Settings()
    provider = FakeProvider()
    tools_service = FakeToolsService()
    mcp_client_service = FakeMcpClientService()
    service = LlmService(
        settings,
        provider,
        tools_service,  # type: ignore[arg-type]
        mcp_client_service,  # type: ignore[arg-type]
    )

    await service.close()

    assert provider.closed is True
    assert tools_service.closed is False
    assert mcp_client_service.closed is False


class MinimalProvider(BaseLlmProvider):
    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        tools: list[BaseTool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return "ok"


@pytest.mark.asyncio
async def test_base_llm_provider_close_defaults_to_noop() -> None:
    assert await MinimalProvider().close() is None
