from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import ValidationError

from app.core.config_store import load_overrides, merge_overrides, save_overrides
from app.core.exceptions import ConfigurationError, ValidationApplicationError
from app.core.settings import Settings
from app.llm.factory import create_llm_provider
from app.memory.providers.in_memory import InMemoryMemoryProvider
from app.memory.providers.redis_memory import RedisMemoryProvider
from app.rag.ingestion.embeddings import EmbeddingService
from app.rag.providers.in_memory_rag import InMemoryRagProvider
from app.rag.providers.redis_rag import RedisRagProvider
from app.services.agent_service import AgentService
from app.services.llm_service import LlmService
from app.services.mcp_client_service import McpClientService
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService
from app.services.tools_service import ToolsService

if TYPE_CHECKING:
    from app.core.lifespan import AppContainer

LLM_FIELDS = {
    "llm_provider",
    "llm_model",
    "llm_temperature",
    "llm_max_tokens",
    "llm_timeout_seconds",
    "openai_api_key",
    "openai_model",
    "ollama_base_url",
    "ollama_model",
    "anthropic_api_key",
    "anthropic_model",
}
AGENT_FIELDS = {"agent_prompt", "default_response_language", "language_detection_enabled"}
MEMORY_FIELDS = {"agent_memory_type", "agent_memory_window", "memory_ttl_seconds", "redis_url"}
RAG_FIELDS = {
    "rag_provider",
    "rag_docs_path",
    "rag_top_k",
    "rag_chunk_size",
    "rag_chunk_overlap",
    "vector_store",
    "vector_index_name",
    "embedding_provider",
    "embedding_model",
    "redis_url",
}
TOOLS_FIELDS = {
    "llm_tools_config",
    "llm_tools_auth_token",
    "llm_tools_auth_header",
    "llm_tools_auth_scheme",
}
MCP_FIELDS = {
    "mcp_servers",
    "mcp_tool_timeout_ms",
    "mcp_throw_on_load_error",
    "mcp_use_standard_content_blocks",
    "mcp_auth_token",
    "mcp_auth_header",
}


@dataclass
class ConfigChangeResult:
    rebuilt: list[str]
    warnings: list[str]
    new_settings: Settings


class ConfigService:
    def __init__(self, container: AppContainer) -> None:
        self._container = container
        self._lock = asyncio.Lock()
        self._logger = structlog.get_logger(__name__)

    async def apply_patch(self, patch: dict[str, Any]) -> ConfigChangeResult:
        async with self._lock:
            current_settings = self._container.settings
            existing_overrides = load_overrides(current_settings.runtime_config_path)
            candidate_overrides = merge_overrides(existing_overrides, patch)
            try:
                new_settings = (
                    Settings(**candidate_overrides) if candidate_overrides else Settings()
                )
                # Force evaluation of the lazily-parsed JSON blobs now, so a malformed
                # llm_tools_config/mcp_servers patch fails before any service is rebuilt.
                _ = new_settings.parsed_http_tools
                _ = new_settings.parsed_mcp_servers
            except (ValidationError, ConfigurationError) as exc:
                raise ValidationApplicationError(str(exc)) from exc

            changed_fields = set(patch.keys())
            rebuilt: list[str] = []
            warnings: list[str] = []

            if changed_fields & MEMORY_FIELDS:
                if current_settings.agent_memory_type != new_settings.agent_memory_type:
                    warnings.append(
                        "Memory backend changed; in-flight session history was not migrated."
                    )
                await self._rebuild_memory(new_settings)
                rebuilt.append("memory")

            if changed_fields & RAG_FIELDS:
                await self._rebuild_rag(new_settings)
                warnings.append("RAG index was rebuilt from rag_docs_path.")
                rebuilt.append("rag")

            tools_rebuilt = False
            if changed_fields & TOOLS_FIELDS:
                await self._rebuild_tools(new_settings)
                tools_rebuilt = True
                rebuilt.append("tools")

            mcp_rebuilt = False
            if changed_fields & MCP_FIELDS:
                await self._rebuild_mcp(new_settings)
                mcp_rebuilt = True
                rebuilt.append("mcp")

            if changed_fields & LLM_FIELDS or tools_rebuilt or mcp_rebuilt:
                await self._rebuild_llm(new_settings)
                rebuilt.append("llm")

            agent_changed = any(
                getattr(current_settings, name) != getattr(new_settings, name)
                for name in AGENT_FIELDS
            )
            if agent_changed:
                await self._container.memory_service.clear_all()
                warnings.append(
                    "All session histories were cleared because agent instructions changed."
                )

            self._container.settings = new_settings
            self._container.agent_service = AgentService(
                new_settings,
                self._container.rag_service,
                self._container.llm_service,
                self._container.memory_service,
            )
            if changed_fields & AGENT_FIELDS and "agent" not in rebuilt:
                rebuilt.append("agent")

            save_overrides(new_settings.runtime_config_path, candidate_overrides)
            self._logger.info("runtime_config_applied", rebuilt=rebuilt)
            return ConfigChangeResult(rebuilt=rebuilt, warnings=warnings, new_settings=new_settings)

    async def _rebuild_memory(self, new_settings: Settings) -> None:
        provider = (
            RedisMemoryProvider(new_settings)
            if new_settings.agent_memory_type == "redis"
            else InMemoryMemoryProvider(new_settings)
        )
        service = MemoryService(provider)
        await service.start()
        old = self._container.memory_service
        self._container.memory_service = service
        await old.close()

    async def _rebuild_rag(self, new_settings: Settings) -> None:
        embedding_service = EmbeddingService(new_settings)
        provider = (
            RedisRagProvider(new_settings, embedding_service)
            if new_settings.rag_provider == "redis"
            else InMemoryRagProvider(new_settings, embedding_service)
        )
        service = RagService(provider)
        await service.start()
        old = self._container.rag_service
        self._container.rag_service = service
        await old.close()

    async def _rebuild_tools(self, new_settings: Settings) -> None:
        try:
            service = ToolsService(new_settings)
        except ConfigurationError as exc:
            raise ValidationApplicationError(str(exc)) from exc
        old = self._container.tools_service
        self._container.tools_service = service
        await old.close()

    async def _rebuild_mcp(self, new_settings: Settings) -> None:
        service = McpClientService(new_settings)
        old = self._container.mcp_client_service
        self._container.mcp_client_service = service
        await old.close()

    async def _rebuild_llm(self, new_settings: Settings) -> None:
        provider = create_llm_provider(new_settings)
        service = LlmService(
            new_settings,
            provider,
            self._container.tools_service,
            self._container.mcp_client_service,
        )
        await service.start()
        old = self._container.llm_service
        self._container.llm_service = service
        await old.close()
