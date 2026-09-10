import asyncio
from pathlib import Path

import pytest

from app.core.config_store import load_overrides
from app.core.exceptions import ValidationApplicationError
from app.core.lifespan import AppContainer, build_container, close_container
from app.core.settings import Settings


async def _build_container(tmp_path: Path) -> AppContainer:
    settings = Settings(
        llm_provider="ollama",
        agent_memory_type="memory",
        rag_provider="in_memory",
        mcp_servers="{}",
        llm_tools_config="[]",
        runtime_config_path=tmp_path / "overrides.json",
    )
    return await build_container(settings)


@pytest.mark.asyncio
async def test_apply_patch_agent_only_rebuilds_agent_service(tmp_path: Path) -> None:
    container = await _build_container(tmp_path)
    try:
        llm_service = container.llm_service
        tools_service = container.tools_service
        memory_service = container.memory_service
        rag_service = container.rag_service
        mcp_client_service = container.mcp_client_service

        result = await container.config_service.apply_patch({"agent_prompt": "New prompt"})

        assert result.rebuilt == ["agent"]
        assert container.settings.agent_prompt == "New prompt"
        assert container.llm_service is llm_service
        assert container.tools_service is tools_service
        assert container.memory_service is memory_service
        assert container.rag_service is rag_service
        assert container.mcp_client_service is mcp_client_service
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_llm_change_rebuilds_only_llm(tmp_path: Path) -> None:
    container = await _build_container(tmp_path)
    try:
        old_llm_service = container.llm_service
        tools_service = container.tools_service
        mcp_client_service = container.mcp_client_service

        result = await container.config_service.apply_patch({"llm_model": "llama3.1:70b"})

        assert result.rebuilt == ["llm"]
        assert container.llm_service is not old_llm_service
        assert container.tools_service is tools_service
        assert container.mcp_client_service is mcp_client_service
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_invalid_tools_json_does_not_rebuild_or_persist(
    tmp_path: Path,
) -> None:
    container = await _build_container(tmp_path)
    try:
        tools_service = container.tools_service
        path = container.settings.runtime_config_path

        with pytest.raises(ValidationApplicationError):
            await container.config_service.apply_patch({"llm_tools_config": "not-json"})

        assert container.tools_service is tools_service
        assert load_overrides(path) == {}
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_mcp_change_cascades_to_llm_but_not_tools(tmp_path: Path) -> None:
    container = await _build_container(tmp_path)
    try:
        old_mcp_client_service = container.mcp_client_service
        old_llm_service = container.llm_service
        tools_service = container.tools_service

        result = await container.config_service.apply_patch({"mcp_servers": "{}"})

        assert set(result.rebuilt) == {"mcp", "llm"}
        assert container.mcp_client_service is not old_mcp_client_service
        assert container.llm_service is not old_llm_service
        assert container.tools_service is tools_service
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_persists_overrides_to_disk(tmp_path: Path) -> None:
    container = await _build_container(tmp_path)
    try:
        await container.config_service.apply_patch({"agent_prompt": "Persisted prompt"})
        overrides = load_overrides(container.settings.runtime_config_path)
        assert overrides["agent_prompt"] == "Persisted prompt"
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_serializes_concurrent_writes(tmp_path: Path) -> None:
    container = await _build_container(tmp_path)
    try:
        await asyncio.gather(
            container.config_service.apply_patch({"agent_prompt": "From A"}),
            container.config_service.apply_patch({"default_response_language": "es"}),
        )
        overrides = load_overrides(container.settings.runtime_config_path)
        assert overrides["agent_prompt"] == "From A"
        assert overrides["default_response_language"] == "es"
    finally:
        await close_container(container)
