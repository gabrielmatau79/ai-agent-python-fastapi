from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.settings import SECRET_FIELDS, Settings


class EffectiveConfigResponse(BaseModel):
    config: dict[str, object]


class LlmConfigSection(BaseModel):
    llm_provider: Literal["openai", "ollama", "anthropic"] = Field(alias="llmProvider")
    llm_model: str = Field(alias="llmModel")
    llm_temperature: float = Field(alias="llmTemperature")
    llm_max_tokens: int = Field(alias="llmMaxTokens")
    llm_timeout_seconds: float = Field(alias="llmTimeoutSeconds")
    openai_api_key_set: bool = Field(alias="openaiApiKeySet")
    openai_model: str = Field(alias="openaiModel")
    ollama_base_url: str = Field(alias="ollamaBaseUrl")
    ollama_model: str = Field(alias="ollamaModel")
    anthropic_api_key_set: bool = Field(alias="anthropicApiKeySet")
    anthropic_model: str = Field(alias="anthropicModel")

    model_config = {"populate_by_name": True}


class AgentConfigSection(BaseModel):
    agent_prompt: str = Field(alias="agentPrompt")
    default_response_language: str = Field(alias="defaultResponseLanguage")
    language_detection_enabled: bool = Field(alias="languageDetectionEnabled")

    model_config = {"populate_by_name": True}


class MemoryConfigSection(BaseModel):
    agent_memory_type: Literal["memory", "redis"] = Field(alias="agentMemoryType")
    agent_memory_window: int = Field(alias="agentMemoryWindow")
    memory_ttl_seconds: int = Field(alias="memoryTtlSeconds")
    redis_url: str = Field(alias="redisUrl")

    model_config = {"populate_by_name": True}


class RagConfigSection(BaseModel):
    rag_provider: Literal["in_memory", "redis"] = Field(alias="ragProvider")
    rag_docs_path: str = Field(alias="ragDocsPath")
    rag_top_k: int = Field(alias="ragTopK")
    rag_chunk_size: int = Field(alias="ragChunkSize")
    rag_chunk_overlap: int = Field(alias="ragChunkOverlap")
    embedding_provider: Literal["openai", "local"] = Field(alias="embeddingProvider")
    embedding_model: str = Field(alias="embeddingModel")
    vector_store: Literal["memory", "redis"] = Field(alias="vectorStore")
    vector_index_name: str = Field(alias="vectorIndexName")

    model_config = {"populate_by_name": True}


class ToolsConfigSection(BaseModel):
    llm_tools_config: str = Field(alias="llmToolsConfig")
    llm_tools_auth_token_set: bool = Field(alias="llmToolsAuthTokenSet")
    llm_tools_auth_header: str = Field(alias="llmToolsAuthHeader")
    llm_tools_auth_scheme: str = Field(alias="llmToolsAuthScheme")

    model_config = {"populate_by_name": True}


class McpConfigSection(BaseModel):
    mcp_servers: str = Field(alias="mcpServers")
    mcp_tool_timeout_ms: int = Field(alias="mcpToolTimeoutMs")
    mcp_throw_on_load_error: bool = Field(alias="mcpThrowOnLoadError")
    mcp_use_standard_content_blocks: bool = Field(alias="mcpUseStandardContentBlocks")
    mcp_auth_token_set: bool = Field(alias="mcpAuthTokenSet")
    mcp_auth_header: str = Field(alias="mcpAuthHeader")

    model_config = {"populate_by_name": True}


class EditableConfigResponse(BaseModel):
    llm: LlmConfigSection
    agent: AgentConfigSection
    memory: MemoryConfigSection
    rag: RagConfigSection
    tools: ToolsConfigSection
    mcp: McpConfigSection


def _is_secret_set(settings: Settings, field_name: str) -> bool:
    assert field_name in SECRET_FIELDS, f"{field_name} is not a declared secret field"
    return getattr(settings, field_name) is not None


def to_editable_sections(settings: Settings) -> EditableConfigResponse:
    return EditableConfigResponse(
        llm=LlmConfigSection(
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_temperature=settings.llm_temperature,
            llm_max_tokens=settings.llm_max_tokens,
            llm_timeout_seconds=settings.llm_timeout_seconds,
            openai_api_key_set=_is_secret_set(settings, "openai_api_key"),
            openai_model=settings.openai_model,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            anthropic_api_key_set=_is_secret_set(settings, "anthropic_api_key"),
            anthropic_model=settings.anthropic_model,
        ),
        agent=AgentConfigSection(
            agent_prompt=settings.agent_prompt,
            default_response_language=settings.default_response_language,
            language_detection_enabled=settings.language_detection_enabled,
        ),
        memory=MemoryConfigSection(
            agent_memory_type=settings.agent_memory_type,
            agent_memory_window=settings.agent_memory_window,
            memory_ttl_seconds=settings.memory_ttl_seconds,
            redis_url=settings.redis_url,
        ),
        rag=RagConfigSection(
            rag_provider=settings.rag_provider,
            rag_docs_path=str(settings.rag_docs_path),
            rag_top_k=settings.rag_top_k,
            rag_chunk_size=settings.rag_chunk_size,
            rag_chunk_overlap=settings.rag_chunk_overlap,
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            vector_store=settings.vector_store,
            vector_index_name=settings.vector_index_name,
        ),
        tools=ToolsConfigSection(
            llm_tools_config=settings.llm_tools_config,
            llm_tools_auth_token_set=_is_secret_set(settings, "llm_tools_auth_token"),
            llm_tools_auth_header=settings.llm_tools_auth_header,
            llm_tools_auth_scheme=settings.llm_tools_auth_scheme,
        ),
        mcp=McpConfigSection(
            mcp_servers=settings.mcp_servers,
            mcp_tool_timeout_ms=settings.mcp_tool_timeout_ms,
            mcp_throw_on_load_error=settings.mcp_throw_on_load_error,
            mcp_use_standard_content_blocks=settings.mcp_use_standard_content_blocks,
            mcp_auth_token_set=_is_secret_set(settings, "mcp_auth_token"),
            mcp_auth_header=settings.mcp_auth_header,
        ),
    )


class ConfigUpdateRequest(BaseModel):
    llm_provider: Literal["openai", "ollama", "anthropic"] | None = Field(
        None, alias="llmProvider"
    )
    llm_model: str | None = Field(None, alias="llmModel")
    llm_temperature: float | None = Field(None, alias="llmTemperature")
    llm_max_tokens: int | None = Field(None, alias="llmMaxTokens")
    llm_timeout_seconds: float | None = Field(None, alias="llmTimeoutSeconds")
    openai_api_key: str | None = Field(None, alias="openaiApiKey")
    openai_model: str | None = Field(None, alias="openaiModel")
    ollama_base_url: str | None = Field(None, alias="ollamaBaseUrl")
    ollama_model: str | None = Field(None, alias="ollamaModel")
    anthropic_api_key: str | None = Field(None, alias="anthropicApiKey")
    anthropic_model: str | None = Field(None, alias="anthropicModel")

    agent_prompt: str | None = Field(None, alias="agentPrompt")
    default_response_language: str | None = Field(None, alias="defaultResponseLanguage")
    language_detection_enabled: bool | None = Field(None, alias="languageDetectionEnabled")

    agent_memory_type: Literal["memory", "redis"] | None = Field(None, alias="agentMemoryType")
    agent_memory_window: int | None = Field(None, alias="agentMemoryWindow")
    memory_ttl_seconds: int | None = Field(None, alias="memoryTtlSeconds")
    redis_url: str | None = Field(None, alias="redisUrl")

    rag_provider: Literal["in_memory", "redis"] | None = Field(None, alias="ragProvider")
    rag_docs_path: str | None = Field(None, alias="ragDocsPath")
    rag_top_k: int | None = Field(None, alias="ragTopK")
    rag_chunk_size: int | None = Field(None, alias="ragChunkSize")
    rag_chunk_overlap: int | None = Field(None, alias="ragChunkOverlap")
    embedding_provider: Literal["openai", "local"] | None = Field(None, alias="embeddingProvider")
    embedding_model: str | None = Field(None, alias="embeddingModel")
    vector_store: Literal["memory", "redis"] | None = Field(None, alias="vectorStore")
    vector_index_name: str | None = Field(None, alias="vectorIndexName")

    llm_tools_config: str | None = Field(None, alias="llmToolsConfig")
    llm_tools_auth_token: str | None = Field(None, alias="llmToolsAuthToken")
    llm_tools_auth_header: str | None = Field(None, alias="llmToolsAuthHeader")
    llm_tools_auth_scheme: str | None = Field(None, alias="llmToolsAuthScheme")

    mcp_servers: str | None = Field(None, alias="mcpServers")
    mcp_tool_timeout_ms: int | None = Field(None, alias="mcpToolTimeoutMs")
    mcp_throw_on_load_error: bool | None = Field(None, alias="mcpThrowOnLoadError")
    mcp_use_standard_content_blocks: bool | None = Field(
        None, alias="mcpUseStandardContentBlocks"
    )
    mcp_auth_token: str | None = Field(None, alias="mcpAuthToken")
    mcp_auth_header: str | None = Field(None, alias="mcpAuthHeader")

    model_config = {"populate_by_name": True}


class ConfigUpdateResponse(BaseModel):
    rebuilt: list[str]
    warnings: list[str]
    config: dict[str, object]
