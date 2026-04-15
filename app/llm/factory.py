from __future__ import annotations

from app.core.settings import Settings
from app.llm.base import BaseLlmProvider
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider


def create_llm_provider(settings: Settings) -> BaseLlmProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(settings)
    return OpenAIProvider(settings)
