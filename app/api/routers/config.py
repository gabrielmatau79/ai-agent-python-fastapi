from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_config_service, get_settings, verify_api_key
from app.core.settings import Settings
from app.schemas.config import (
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    EditableConfigResponse,
    EffectiveConfigResponse,
    to_editable_sections,
)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/effective-sanitized", response_model=EffectiveConfigResponse)
async def effective_config(
    _: None = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> EffectiveConfigResponse:
    return EffectiveConfigResponse(config=settings.sanitized_dict())


@router.get("/editable", response_model=EditableConfigResponse)
async def editable_config(
    _: None = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> EditableConfigResponse:
    return to_editable_sections(settings)


@router.patch("", response_model=ConfigUpdateResponse)
async def update_config(
    payload: ConfigUpdateRequest,
    _: None = Depends(verify_api_key),
    config_service: Any = Depends(get_config_service),
) -> ConfigUpdateResponse:
    result = await config_service.apply_patch(payload.model_dump(exclude_unset=True))
    return ConfigUpdateResponse(
        rebuilt=result.rebuilt,
        warnings=result.warnings,
        config=result.new_settings.sanitized_dict(),
    )
