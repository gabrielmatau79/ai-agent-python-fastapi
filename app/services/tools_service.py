from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import quote

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.exceptions import ConfigurationError
from app.core.settings import HttpToolConfig, Settings


class QueryInput(BaseModel):
    query: str = Field(min_length=1)


class ToolsService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
        self._tools = self._build_tools()

    def get_tools(self) -> list[StructuredTool]:
        return list(self._tools)

    async def close(self) -> None:
        await self._client.aclose()

    def _build_tools(self) -> list[StructuredTool]:
        tools = [self._current_time_tool()]
        for config in self._settings.parsed_http_tools:
            tools.append(self._http_tool(config))
        return tools

    def _current_time_tool(self) -> StructuredTool:
        async def _get_current_time(query: str) -> str:
            _ = query
            return datetime.now(UTC).isoformat()

        return StructuredTool.from_function(
            coroutine=_get_current_time,
            name="get_current_time",
            description="Returns the current date and time in ISO 8601 format.",
            args_schema=QueryInput,
        )

    def _http_tool(self, config: HttpToolConfig) -> StructuredTool:
        async def _call_http_tool(query: str) -> str:
            url = config.endpoint
            encoded_query = quote(query)
            if "{query}" in url:
                url = url.replace("{query}", encoded_query)
            elif config.method == "GET":
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}q={encoded_query}"

            headers: dict[str, str] = {}
            if config.requires_auth:
                token = self._settings.llm_tools_auth_token
                if token is None:
                    return f"ERROR calling {config.name}: missing auth token"
                auth_token = token.get_secret_value()
                scheme = self._settings.llm_tools_auth_scheme.strip()
                value = f"{scheme} {auth_token}".strip() if scheme else auth_token
                headers[self._settings.llm_tools_auth_header] = value

            try:
                if config.method == "GET":
                    response = await self._client.request(config.method, url, headers=headers)
                else:
                    response = await self._client.request(
                        config.method,
                        url,
                        headers=headers,
                        json={"query": query},
                    )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                return f"ERROR calling {config.name}: {exc}"

            try:
                return json.dumps(response.json(), ensure_ascii=True)
            except ValueError:
                return response.text

        return StructuredTool.from_function(
            coroutine=_call_http_tool,
            name=config.name,
            description=config.description,
            args_schema=QueryInput,
        )


def validate_tools_config(settings: Settings) -> list[HttpToolConfig]:
    try:
        return settings.parsed_http_tools
    except ConfigurationError:
        raise
