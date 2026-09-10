from __future__ import annotations

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from app.core.exceptions import ExternalServiceError
from app.core.settings import Settings
from app.llm.base import BaseLlmProvider


class OllamaProvider(BaseLlmProvider):
    supports_tools = False

    def __init__(self, settings: Settings) -> None:
        self._client = ChatOllama(
            model=settings.effective_llm_model(),
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_max_tokens,
        )

    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        tools: list[BaseTool] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        _ = tools
        _ = metadata
        try:
            # ChatOllama already manages invocation metadata internally; passing it
            # through here can conflict with the underlying LangChain call path.
            result = await self._client.ainvoke(messages)
            return str(result.content).strip()
        except Exception as exc:  # pragma: no cover
            raise ExternalServiceError(f"Ollama generation failed: {exc}") from exc
