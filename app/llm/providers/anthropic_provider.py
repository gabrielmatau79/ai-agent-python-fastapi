from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.core.settings import Settings
from app.llm.base import BaseLlmProvider


class AnthropicProvider(BaseLlmProvider):
    supports_tools = True

    def __init__(self, settings: Settings) -> None:
        if settings.anthropic_api_key is None:
            raise ConfigurationError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic.")
        self._client = ChatAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
            model=settings.effective_llm_model(),
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_tokens=settings.llm_max_tokens,
        )

    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        tools: list[BaseTool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        _ = metadata
        try:
            if not tools:
                result = await self._client.ainvoke(messages)
                return str(result.content).strip()

            tool_enabled = self._client.bind_tools(tools)
            conversation = list(messages)
            response: AIMessage = await tool_enabled.ainvoke(conversation)
            while getattr(response, "tool_calls", None):
                conversation.append(response)
                for tool_call in response.tool_calls:
                    tool = next(
                        (candidate for candidate in tools if candidate.name == tool_call["name"]),
                        None,
                    )
                    if tool is None:
                        continue
                    result = await tool.ainvoke(tool_call.get("args", {}))
                    conversation.append(
                        ToolMessage(
                            content=result if isinstance(result, str) else str(result),
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                        )
                    )
                response = await tool_enabled.ainvoke(conversation)
            return str(response.content).strip()
        except Exception as exc:  # pragma: no cover
            raise ExternalServiceError(f"Anthropic generation failed: {exc}") from exc
