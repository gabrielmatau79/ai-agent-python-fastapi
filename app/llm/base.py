from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool


class BaseLlmProvider(ABC):
    supports_tools: bool = False

    @abstractmethod
    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        tools: list[BaseTool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError
