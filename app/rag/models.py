from __future__ import annotations

from pydantic import BaseModel


class SourceDocument(BaseModel):
    source: str
    content: str


class IndexedChunk(BaseModel):
    id: str
    source: str
    content: str
    embedding: list[float]


class RetrievalResult(BaseModel):
    source: str
    content: str
    score: float
