from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class RecordingLlmService:
    def __init__(self) -> None:
        self.received_messages: list[Any] = []

    async def generate(self, messages: list[Any], *, session_id: str) -> str:
        self.received_messages = messages
        return f"mocked answer for {session_id}"

    async def close(self) -> None:
        return


@asynccontextmanager
async def build_client() -> AsyncIterator[tuple[AsyncClient, RecordingLlmService]]:
    app = create_app()
    async with app.router.lifespan_context(app):
        recording = RecordingLlmService()
        app.state.container.llm_service = recording
        app.state.container.agent_service._llm_service = recording
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client, recording


def _base_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_PROVIDER", "in_memory")
    monkeypatch.setenv("AGENT_MEMORY_TYPE", "memory")
    monkeypatch.setenv("MCP_SERVERS", "{}")
    monkeypatch.setenv("RUNTIME_CONFIG_PATH", str(tmp_path / "overrides.json"))


@pytest.mark.asyncio
async def test_patch_config_agent_prompt_updates_running_agent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _base_env(monkeypatch, tmp_path)
    async with build_client() as (client, recording):
        response = await client.patch(
            "/api/v1/config", json={"agentPrompt": "You only answer in pirate speak."}
        )
        assert response.status_code == 200
        assert response.json()["rebuilt"] == ["agent"]

        ask_response = await client.post(
            "/api/v1/agent/ask",
            json={"userInput": "hi", "sessionId": "s-admin-1", "userLang": "en"},
        )
        assert ask_response.status_code == 200

    system_message = recording.received_messages[0]
    assert "pirate speak" in system_message.content


@pytest.mark.asyncio
async def test_patch_config_invalid_tools_json_returns_400(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _base_env(monkeypatch, tmp_path)
    async with build_client() as (client, _recording):
        response = await client.patch("/api/v1/config", json={"llmToolsConfig": "not-json"})
        assert response.status_code == 400

        effective = await client.get("/api/v1/config/effective-sanitized")
        assert effective.json()["config"]["llm_tools_config"] == "[]"


@pytest.mark.asyncio
async def test_patch_config_requires_api_key_when_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("API_KEY_ENABLED", "true")
    monkeypatch.setenv("API_KEY_VALUE", "secret-key")
    async with build_client() as (client, _recording):
        unauthorized = await client.patch("/api/v1/config", json={"agentPrompt": "x"})
        assert unauthorized.status_code == 401

        authorized = await client.patch(
            "/api/v1/config",
            json={"agentPrompt": "x"},
            headers={"X-API-Key": "secret-key"},
        )
        assert authorized.status_code == 200


@pytest.mark.asyncio
async def test_admin_page_renders_all_sections(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _base_env(monkeypatch, tmp_path)
    async with build_client() as (client, _recording):
        response = await client.get("/admin/")
        assert response.status_code == 200
        for marker in ("LLM", "Agent", "Memory", "RAG", "Tools", "MCP"):
            assert marker in response.text


@pytest.mark.asyncio
async def test_get_editable_config_never_leaks_secrets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-leak")
    async with build_client() as (client, _recording):
        response = await client.get("/api/v1/config/editable")
        assert response.status_code == 200
        assert "sk-should-not-leak" not in response.text
        assert response.json()["llm"]["openaiApiKeySet"] is True
