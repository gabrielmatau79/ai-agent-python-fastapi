from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.settings import Settings
from app.memory.providers.in_memory import InMemoryMemoryProvider
from app.rag.ingestion.embeddings import EmbeddingService
from app.rag.providers.in_memory_rag import InMemoryRagProvider
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService


class QueryRagInput(BaseModel):
    query: str = Field(min_length=1)


class SessionInput(BaseModel):
    session_id: str = Field(alias="sessionId", min_length=1)

    model_config = {"populate_by_name": True}


class AddMemoryInput(SessionInput):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


def build_local_services() -> tuple[RagService, MemoryService]:
    settings = Settings()
    embedding_service = EmbeddingService(settings)
    rag_provider = InMemoryRagProvider(settings, embedding_service)
    memory_provider = InMemoryMemoryProvider(settings)
    return RagService(rag_provider), MemoryService(memory_provider)
