from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.core.settings import Settings
from app.llm.base import BaseLlmProvider


class OpenAIProvider(BaseLlmProvider):
    supports_tools = True

    def __init__(self, settings: Settings) -> None:
        if settings.openai_api_key is None:
            raise ConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        self._client = ChatOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
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
        try:
            if not tools:
                result = await self._client.ainvoke(messages, metadata=metadata)
                return str(result.content).strip()

            tool_enabled = self._client.bind_tools(tools)
            conversation = list(messages)
            response: AIMessage = await tool_enabled.ainvoke(conversation, metadata=metadata)
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
                            content=_normalize_tool_result(result),
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                        )
                    )
                response = await tool_enabled.ainvoke(conversation, metadata=metadata)
            return str(response.content).strip()
        except Exception as exc:  # pragma: no cover - provider errors are integration-dependent
            raise ExternalServiceError(f"OpenAI generation failed: {exc}") from exc


def _normalize_tool_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    return str(result)
