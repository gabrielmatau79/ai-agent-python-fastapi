from typing import Any, cast

from fastapi import Depends, HTTPException, Request, status

from app.core.settings import Settings


async def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.container.settings)


async def verify_api_key(request: Request, settings: Settings = Depends(get_settings)) -> None:
    if not settings.api_key_enabled:
        return
    provided = request.headers.get(settings.api_key_header_name)
    if provided != settings.api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


async def get_agent_service(request: Request) -> Any:
    return request.app.state.container.agent_service


async def get_memory_service(request: Request) -> Any:
    return request.app.state.container.memory_service


async def get_rag_service(request: Request) -> Any:
    return request.app.state.container.rag_service
