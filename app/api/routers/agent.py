from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_agent_service, verify_api_key
from app.schemas.agent import AgentAskRequest, AgentAskResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/ask", response_model=AgentAskResponse)
async def ask_agent(
    payload: AgentAskRequest,
    _: None = Depends(verify_api_key),
    agent_service: Any = Depends(get_agent_service),
) -> AgentAskResponse:
    answer = await agent_service.ask(payload)
    return AgentAskResponse(answer=answer)
