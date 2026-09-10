import asyncio
from pathlib import Path

import pytest

from app.core.config_store import load_overrides
from app.core.exceptions import ValidationApplicationError
from app.core.lifespan import AppContainer, build_container, close_container
from app.core.settings import Settings


def _set_base_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # These must be env vars (not Settings(**kwargs)) because ConfigService
    # rebuilds Settings from scratch on every apply_patch() call — only env
    # vars and persisted overrides survive that reconstruction, kwargs don't.
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("AGENT_MEMORY_TYPE", "memory")
    monkeypatch.setenv("RAG_PROVIDER", "in_memory")
    monkeypatch.setenv("MCP_SERVERS", "{}")
    monkeypatch.setenv("LLM_TOOLS_CONFIG", "[]")
    monkeypatch.setenv("RUNTIME_CONFIG_PATH", str(tmp_path / "overrides.json"))


async def _build_container(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppContainer:
    _set_base_env(monkeypatch, tmp_path)
    return await build_container(Settings())


@pytest.mark.asyncio
async def test_apply_patch_agent_only_rebuilds_agent_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
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
async def test_apply_patch_llm_change_rebuilds_only_llm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
    try:
        old_llm_service = container.llm_service
        tools_service = container.tools_service
        mcp_client_service = container.mcp_client_service

        result = await container.config_service.apply_patch({"llm_model": "llama3.1:70b"})

        assert result.rebuilt == ["llm"]
        assert container.settings.llm_provider == "ollama"
        assert container.llm_service is not old_llm_service
        assert container.tools_service is tools_service
        assert container.mcp_client_service is mcp_client_service
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_invalid_tools_json_does_not_rebuild_or_persist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
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
async def test_apply_patch_mcp_change_cascades_to_llm_but_not_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
    try:
        old_mcp_client_service = container.mcp_client_service
        old_llm_service = container.llm_service
        tools_service = container.tools_service

        result = await container.config_service.apply_patch({"mcp_servers": "{}"})

        assert set(result.rebuilt) == {"mcp", "llm"}
        assert container.settings.llm_provider == "ollama"
        assert container.mcp_client_service is not old_mcp_client_service
        assert container.llm_service is not old_llm_service
        assert container.tools_service is tools_service
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_persists_overrides_to_disk(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
    try:
        await container.config_service.apply_patch({"agent_prompt": "Persisted prompt"})
        overrides = load_overrides(container.settings.runtime_config_path)
        assert overrides["agent_prompt"] == "Persisted prompt"
    finally:
        await close_container(container)


@pytest.mark.asyncio
async def test_apply_patch_serializes_concurrent_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    container = await _build_container(monkeypatch, tmp_path)
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
