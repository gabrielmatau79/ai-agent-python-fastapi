from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_rag_service, verify_api_key
from app.schemas.rag import RagReindexResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/reindex", response_model=RagReindexResponse)
async def reindex_rag(
    _: None = Depends(verify_api_key),
    rag_service: Any = Depends(get_rag_service),
) -> RagReindexResponse:
    documents_indexed, chunks_indexed = await rag_service.reindex()
    return RagReindexResponse(documents_indexed=documents_indexed, chunks_indexed=chunks_indexed)
