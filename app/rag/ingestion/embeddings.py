from __future__ import annotations

import hashlib
import math
import re

from langchain_openai import OpenAIEmbeddings

from app.core.settings import Settings


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._remote = None
        if settings.embedding_provider == "openai" and settings.openai_api_key is not None:
            self._remote = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key.get_secret_value(),
                model=settings.embedding_model,
            )

    async def embed(self, text: str) -> list[float]:
        if self._remote is not None:
            return list(await self._remote.aembed_query(text))
        return _hashed_embedding(text)


def _hashed_embedding(text: str, dimensions: int = 128) -> list[float]:
    vector = [0.0] * dimensions
    tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
