from pydantic import BaseModel


class EffectiveConfigResponse(BaseModel):
    config: dict[str, object]
