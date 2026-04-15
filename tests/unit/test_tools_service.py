import pytest

from app.core.settings import Settings
from app.services.tools_service import ToolsService


def test_tools_config_parsing() -> None:
    settings = Settings(
        llm_tools_config='[{"name":"getZipInfo","description":"zip","endpoint":"https://example.com/{query}","method":"GET","requiresAuth":false}]'
    )
    service = ToolsService(settings)
    tools = service.get_tools()
    assert {tool.name for tool in tools} == {"get_current_time", "getZipInfo"}


@pytest.mark.asyncio
async def test_current_time_tool_returns_string() -> None:
    settings = Settings(llm_tools_config="[]")
    service = ToolsService(settings)
    tool = next(item for item in service.get_tools() if item.name == "get_current_time")
    result = await tool.ainvoke({"query": "ignored"})
    assert "T" in result
    await service.close()
