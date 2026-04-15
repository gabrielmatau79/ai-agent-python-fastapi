from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import structlog
from fastapi import FastAPI

from app.core.logging import configure_logging
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


@dataclass
class AppContainer:
    settings: Settings
    tools_service: ToolsService
    mcp_client_service: McpClientService
    llm_service: LlmService
    memory_service: MemoryService
    rag_service: RagService
    agent_service: AgentService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    configure_logging(settings.log_level)
    logger = structlog.get_logger(__name__)
    embedding_service = EmbeddingService(settings)
    tools_service = ToolsService(settings)
    mcp_client_service = McpClientService(settings)
    llm_provider = create_llm_provider(settings)
    llm_service = LlmService(settings, llm_provider, tools_service, mcp_client_service)

    memory_provider = (
        RedisMemoryProvider(settings)
        if settings.agent_memory_type == "redis"
        else InMemoryMemoryProvider(settings)
    )
    rag_provider = (
        RedisRagProvider(settings, embedding_service)
        if settings.rag_provider == "redis"
        else InMemoryRagProvider(settings, embedding_service)
    )

    memory_service = MemoryService(memory_provider)
    rag_service = RagService(rag_provider)
    agent_service = AgentService(settings, rag_service, llm_service, memory_service)

    await memory_service.start()
    await rag_service.start()
    await llm_service.start()

    app.state.container = AppContainer(
        settings=settings,
        tools_service=tools_service,
        mcp_client_service=mcp_client_service,
        llm_service=llm_service,
        memory_service=memory_service,
        rag_service=rag_service,
        agent_service=agent_service,
    )
    logger.info("application_started", app_name=settings.app_name, env=settings.app_env)
    try:
        yield
    finally:
        await llm_service.close()
        await rag_service.close()
        await memory_service.close()
        logger.info("application_stopped")
