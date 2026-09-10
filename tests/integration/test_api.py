from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class FakeLlmService:
    async def generate(self, messages: list[Any], *, session_id: str) -> str:
        return f"mocked answer for {session_id}: {messages[-1].content}"

    async def close(self) -> None:
        return


@asynccontextmanager
async def build_client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        app.state.container.llm_service = FakeLlmService()
        app.state.container.agent_service._llm_service = app.state.container.llm_service
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


@pytest.mark.asyncio
async def test_agent_ask_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_PROVIDER", "in_memory")
    monkeypatch.setenv("AGENT_MEMORY_TYPE", "memory")
    async with build_client() as client:
        response = await client.post(
            "/api/v1/agent/ask",
            json={
                "userInput": "What is Kubernetes?",
                "sessionId": "session-abc123",
                "userLang": "en",
            },
        )
        assert response.status_code == 200
        assert "mocked answer" in response.json()["answer"]


@pytest.mark.asyncio
async def test_memory_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_PROVIDER", "in_memory")
    monkeypatch.setenv("AGENT_MEMORY_TYPE", "memory")
    async with build_client() as client:
        await client.post(
            "/api/v1/agent/ask",
            json={"userInput": "hello", "sessionId": "mem-1", "userLang": "en"},
        )
        get_response = await client.get("/api/v1/memory/mem-1")
        assert get_response.status_code == 200
        assert len(get_response.json()["history"]) == 2
        delete_response = await client.delete("/api/v1/memory/mem-1")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_rag_reindex_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_PROVIDER", "in_memory")
    monkeypatch.setenv("AGENT_MEMORY_TYPE", "memory")
    async with build_client() as client:
        response = await client.post("/api/v1/rag/reindex")
        assert response.status_code == 200
        assert response.json()["documents_indexed"] >= 1
