from __future__ import annotations

from typing import cast

import structlog
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from app.core.settings import Settings
from app.llm.base import BaseLlmProvider
from app.services.mcp_client_service import McpClientService
from app.services.tools_service import ToolsService


class LlmService:
    def __init__(
        self,
        settings: Settings,
        provider: BaseLlmProvider,
        tools_service: ToolsService,
        mcp_client_service: McpClientService,
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._tools_service = tools_service
        self._mcp_client_service = mcp_client_service
        self._logger = structlog.get_logger(__name__)
        self._tools = cast(list[BaseTool], self._tools_service.get_tools())

    async def start(self) -> None:
        mcp_tools = await self._mcp_client_service.load_tools()
        self._tools.extend(mcp_tools)
        if self._tools and not self._provider.supports_tools:
            self._logger.warning(
                "tools_not_supported_by_provider",
                provider=self._settings.llm_provider,
                tool_count=len(self._tools),
            )

    async def close(self) -> None:
        await self._tools_service.close()
        await self._mcp_client_service.close()

    async def generate(self, messages: list[BaseMessage], *, session_id: str) -> str:
        _ = session_id
        tools = self._tools if self._provider.supports_tools else None
        return await self._provider.generate(messages, tools=tools)
