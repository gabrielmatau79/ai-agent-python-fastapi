from pydantic import BaseModel


class MemoryMessage(BaseModel):
    role: str
    content: str


class MemoryHistoryResponse(BaseModel):
    session_id: str
    history: list[MemoryMessage]

    model_config = {"populate_by_name": True}


class MemoryClearResponse(BaseModel):
    session_id: str
    cleared: bool = True

    model_config = {"populate_by_name": True}
