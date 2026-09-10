from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    user_input: str = Field(alias="userInput", min_length=1)
    session_id: str = Field(alias="sessionId", min_length=1)
    user_lang: str | None = Field(default=None, alias="userLang")

    model_config = {"populate_by_name": True}


class AgentAskResponse(BaseModel):
    answer: str
