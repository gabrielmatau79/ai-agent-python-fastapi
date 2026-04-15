from fastapi import APIRouter, Request

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, object]:
    container = request.app.state.container
    return {
        "status": "ready",
        "memory_backend": container.settings.agent_memory_type,
        "rag_provider": container.settings.rag_provider,
        "llm_provider": container.settings.llm_provider,
    }
