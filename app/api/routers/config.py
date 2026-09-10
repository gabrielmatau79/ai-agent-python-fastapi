from fastapi import APIRouter, Depends

from app.api.deps import get_settings, verify_api_key
from app.core.settings import Settings
from app.schemas.config import EffectiveConfigResponse

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/effective-sanitized", response_model=EffectiveConfigResponse)
async def effective_config(
    _: None = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> EffectiveConfigResponse:
    return EffectiveConfigResponse(config=settings.sanitized_dict())
