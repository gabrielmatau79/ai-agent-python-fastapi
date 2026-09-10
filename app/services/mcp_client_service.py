from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any, cast

import structlog
from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel, Field, create_model

from app.core.settings import McpServerConfig, Settings


class McpClientService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = structlog.get_logger(__name__)
        self._clients: dict[str, tuple[AsyncExitStack, ClientSession]] = {}
        self._tools: dict[str, StructuredTool] = {}

    async def load_tools(self) -> list[StructuredTool]:
        if self._tools:
            return list(self._tools.values())
        tools: list[StructuredTool] = []
        for server_name, config in self._settings.parsed_mcp_servers.items():
            try:
                session = await self._connect_server(server_name, config)
                response = await session.list_tools()
                for tool in response.tools:
                    wrapped = self._wrap_tool(
                        server_name,
                        tool.name,
                        tool.description or "",
                        getattr(tool, "inputSchema", {}) or {},
                    )
                    tools.append(wrapped)
                    self._tools[wrapped.name] = wrapped
            except Exception as exc:
                if config.optional:
                    self._logger.warning(
                        "mcp_server_optional_load_failed", server=server_name, error=str(exc)
                    )
                    continue
                self._logger.error("mcp_server_load_failed", server=server_name, error=str(exc))
                if self._settings.mcp_throw_on_load_error:
                    raise
        return tools

    def get_tool(self, name: str) -> StructuredTool | None:
        return self._tools.get(name)

    async def close(self) -> None:
        for stack, _session in self._clients.values():
            await stack.aclose()
        self._clients.clear()
        self._tools.clear()

    async def _connect_server(self, server_name: str, config: McpServerConfig) -> ClientSession:
        existing = self._clients.get(server_name)
        if existing:
            return existing[1]

        stack = AsyncExitStack()
        if config.transport == "stdio":
            read_stream, write_stream = await stack.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=config.command or "",
                        args=config.args,
                    )
                )
            )
        elif config.transport == "sse":
            timeout_seconds = (
                config.default_tool_timeout or self._settings.mcp_tool_timeout_ms
            ) / 1000
            read_stream, write_stream = await stack.enter_async_context(
                sse_client(
                    config.url or "",
                    headers=config.headers,
                    timeout=timeout_seconds,
                )
            )
        else:
            stream_context = await stack.enter_async_context(
                streamable_http_client(config.url or "")
            )
            read_stream, write_stream = stream_context[0], stream_context[1]

        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        self._clients[server_name] = (stack, session)
        return session

    def _wrap_tool(
        self, server_name: str, tool_name: str, description: str, schema: dict[str, Any]
    ) -> StructuredTool:
        args_schema = _schema_from_json_schema(f"{server_name}_{tool_name}_schema", schema)

        async def _call_tool(**kwargs: Any) -> str:
            session = self._clients[server_name][1]
            result = await session.call_tool(tool_name, kwargs)
            content = getattr(result, "content", [])
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if hasattr(block, "text"):
                        parts.append(str(block.text))
                    else:
                        parts.append(str(block))
                return "\n".join(parts)
            return str(content)

        return StructuredTool.from_function(
            coroutine=_call_tool,
            name=tool_name,
            description=description,
            args_schema=args_schema,
        )


def _schema_from_json_schema(model_name: str, schema: dict[str, Any]) -> type[BaseModel]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields: dict[str, tuple[Any, Any]] = {}
    for name, prop in properties.items():
        json_type = prop.get("type", "string")
        annotation: Any
        if json_type == "integer":
            annotation = int
        elif json_type == "number":
            annotation = float
        elif json_type == "boolean":
            annotation = bool
        elif json_type == "array":
            annotation = list[Any]
        elif json_type == "object":
            annotation = dict[str, Any]
        else:
            annotation = str
        default = ... if name in required else None
        fields[name] = (
            annotation | None if default is None else annotation,
            Field(default=default),
        )
    if not fields:
        fields["query"] = (str | None, Field(default=None))
    return cast(type[BaseModel], create_model(model_name, **cast(dict[str, Any], fields)))
