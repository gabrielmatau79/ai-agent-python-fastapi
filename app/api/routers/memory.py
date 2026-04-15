from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_memory_service, verify_api_key
from app.schemas.memory import MemoryClearResponse, MemoryHistoryResponse, MemoryMessage

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{session_id}", response_model=MemoryHistoryResponse)
async def get_memory(
    session_id: str,
    _: None = Depends(verify_api_key),
    memory_service: Any = Depends(get_memory_service),
) -> MemoryHistoryResponse:
    history = await memory_service.get_history(session_id)
    return MemoryHistoryResponse(
        session_id=session_id,
        history=[MemoryMessage(role=item.role, content=item.content) for item in history],
    )


@router.delete("/{session_id}", response_model=MemoryClearResponse)
async def clear_memory(
    session_id: str,
    _: None = Depends(verify_api_key),
    memory_service: Any = Depends(get_memory_service),
) -> MemoryClearResponse:
    await memory_service.clear(session_id)
    return MemoryClearResponse(session_id=session_id)
