from pydantic import BaseModel


class RagReindexResponse(BaseModel):
    documents_indexed: int
    chunks_indexed: int

    model_config = {"populate_by_name": True}


class RagDocumentResult(BaseModel):
    content: str
    score: float
    source: str


class RagQueryResponse(BaseModel):
    query: str
    results: list[RagDocumentResult]
