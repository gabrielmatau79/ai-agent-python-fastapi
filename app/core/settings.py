from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError

SECRET_FIELDS = frozenset(
    {
        "openai_api_key",
        "anthropic_api_key",
        "llm_tools_auth_token",
        "mcp_auth_token",
        "api_key_value",
    }
)


class HttpToolConfig(BaseModel):
    name: str
    description: str
    endpoint: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    requires_auth: bool = Field(default=False, alias="requiresAuth")


class McpServerRestartConfig(BaseModel):
    enabled: bool = True
    max_attempts: int = 3
    delay_ms: int = 1000


class McpServerConfig(BaseModel):
    transport: Literal["stdio", "http", "streamable_http", "sse"]
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    default_tool_timeout: int | None = None
    optional: bool = False
    restart: McpServerRestartConfig = Field(default_factory=McpServerRestartConfig)

    @model_validator(mode="after")
    def validate_transport_fields(self) -> McpServerConfig:
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio MCP servers require a command")
        if self.transport != "stdio" and not self.url:
            raise ValueError("HTTP/SSE MCP servers require a url")
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Agent FastAPI"
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    agent_prompt: str = (
        "You are a helpful AI assistant. "
        "Use retrieved knowledge when relevant, be honest about uncertainty, "
        "and avoid inventing facts."
    )
    default_response_language: str = "en"
    language_detection_enabled: bool = True

    llm_provider: Literal["openai", "ollama", "anthropic"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 900
    llm_timeout_seconds: float = 45.0

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"

    agent_memory_type: Literal["memory", "redis"] = "memory"
    agent_memory_window: int = 8
    memory_ttl_seconds: int = 14400
    redis_url: str = "redis://localhost:6379/0"

    rag_provider: Literal["in_memory", "redis"] = "in_memory"
    rag_docs_path: Path = Path("sample_docs")
    rag_top_k: int = 3
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    embedding_provider: Literal["openai", "local"] = "local"
    embedding_model: str = "text-embedding-3-small"
    vector_store: Literal["memory", "redis"] = "memory"
    vector_index_name: str = "agent-ia"

    llm_tools_config: str = "[]"
    llm_tools_auth_token: SecretStr | None = None
    llm_tools_auth_header: str = "Authorization"
    llm_tools_auth_scheme: str = "Bearer"

    mcp_servers: str = "{}"
    mcp_tool_timeout_ms: int = 20000
    mcp_throw_on_load_error: bool = False
    mcp_use_standard_content_blocks: bool = True
    mcp_auth_token: SecretStr | None = None
    mcp_auth_header: str = "Authorization"

    api_key_enabled: bool = False
    api_key_header_name: str = "X-API-Key"
    api_key_value: SecretStr | None = None

    runtime_config_path: Path = Path("config/runtime-overrides.json")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ["*"]
            if stripped.startswith("["):
                return json.loads(stripped)
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return value

    @field_validator("rag_docs_path", mode="before")
    @classmethod
    def normalize_docs_path(cls, value: Any) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))

    @cached_property
    def parsed_http_tools(self) -> list[HttpToolConfig]:
        try:
            raw = json.loads(self.llm_tools_config or "[]")
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"LLM_TOOLS_CONFIG contains invalid JSON: {exc.msg}") from exc
        if not isinstance(raw, list):
            raise ConfigurationError("LLM_TOOLS_CONFIG must be a JSON array.")
        return [HttpToolConfig.model_validate(item) for item in raw]

    @cached_property
    def parsed_mcp_servers(self) -> dict[str, McpServerConfig]:
        try:
            raw = json.loads(self.mcp_servers or "{}")
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"MCP_SERVERS contains invalid JSON: {exc.msg}") from exc
        if not isinstance(raw, dict):
            raise ConfigurationError("MCP_SERVERS must be a JSON object keyed by server name.")
        servers = {name: McpServerConfig.model_validate(value) for name, value in raw.items()}
        for server in servers.values():
            if server.default_tool_timeout is None:
                server.default_tool_timeout = self.mcp_tool_timeout_ms
            if (
                server.transport != "stdio"
                and self.mcp_auth_token
                and self.mcp_auth_header not in server.headers
            ):
                token = self.mcp_auth_token.get_secret_value()
                server.headers[self.mcp_auth_header] = f"Bearer {token}"
        return servers

    def effective_llm_model(self) -> str:
        if self.llm_provider == "openai":
            return self.openai_model or self.llm_model
        if self.llm_provider == "ollama":
            return self.ollama_model or self.llm_model
        return self.anthropic_model or self.llm_model

    def sanitized_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        for field_name in SECRET_FIELDS:
            if data.get(field_name):
                data[field_name] = "***REDACTED***"
        return data
