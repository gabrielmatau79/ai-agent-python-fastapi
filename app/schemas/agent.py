from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    user_input: str = Field(
        alias="userInput", min_length=1, examples=["What is the capital of France?"]
    )
    session_id: str = Field(
        alias="sessionId",
        min_length=1,
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    user_lang: str | None = Field(
        default=None, alias="userLang", examples=["en", "es", "fr"]
    )

    model_config = {"populate_by_name": True}


class AgentAskResponse(BaseModel):
    answer: str
