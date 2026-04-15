from __future__ import annotations

import asyncio
import os

from mcp.server.fastmcp import FastMCP

from app.mcp_server.tools import AddMemoryInput, QueryRagInput, SessionInput, build_local_services

mcp = FastMCP("ai-agent-fastapi-local", json_response=True)
_rag_service, _memory_service = build_local_services()


@mcp.tool()
async def query_rag(query: str) -> dict[str, object]:
    payload = QueryRagInput(query=query)
    results = await _rag_service.retrieve(payload.query)
    return {
        "query": payload.query,
        "results": [result.model_dump() for result in results],
    }


@mcp.tool()
async def get_memory_history(sessionId: str) -> dict[str, object]:
    payload = SessionInput(session_id=sessionId)
    history = await _memory_service.get_history(payload.session_id)
    return {"sessionId": payload.session_id, "history": [item.model_dump() for item in history]}


@mcp.tool()
async def add_memory_message(sessionId: str, role: str, content: str) -> dict[str, object]:
    payload = AddMemoryInput(session_id=sessionId, role=role, content=content)
    await _memory_service.add_message(payload.session_id, payload.role, payload.content)
    return {"ok": True, "sessionId": payload.session_id}


@mcp.tool()
async def clear_memory(sessionId: str) -> dict[str, object]:
    payload = SessionInput(session_id=sessionId)
    await _memory_service.clear(payload.session_id)
    return {"ok": True, "sessionId": payload.session_id}


async def _startup() -> None:
    await _memory_service.start()
    await _rag_service.start()


async def _shutdown() -> None:
    await _rag_service.close()
    await _memory_service.close()


def main() -> None:
    asyncio.run(_startup())
    try:
        transport = os.getenv("LOCAL_MCP_TRANSPORT", "stdio")
        if transport == "streamable-http":
            mcp.run(transport="streamable-http")
        else:
            mcp.run()
    finally:
        asyncio.run(_shutdown())


if __name__ == "__main__":
    main()
