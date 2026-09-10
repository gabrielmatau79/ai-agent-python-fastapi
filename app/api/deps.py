from typing import Any, cast

from fastapi import Depends, HTTPException, Request, status

from app.core.settings import Settings


async def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.container.settings)


def _api_key_valid(request: Request, settings: Settings, provided: str | None) -> bool:
    if not settings.api_key_enabled:
        return True
    _ = request
    expected = settings.api_key_value.get_secret_value() if settings.api_key_value else None
    return provided is not None and provided == expected


async def verify_api_key(request: Request, settings: Settings = Depends(get_settings)) -> None:
    provided = request.headers.get(settings.api_key_header_name)
    if not _api_key_valid(request, settings, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


async def verify_api_key_for_page(
    request: Request, settings: Settings = Depends(get_settings)
) -> None:
    provided = request.headers.get(settings.api_key_header_name) or request.query_params.get(
        "key"
    )
    if not _api_key_valid(request, settings, provided):
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


async def get_config_service(request: Request) -> Any:
    return request.app.state.container.config_service
