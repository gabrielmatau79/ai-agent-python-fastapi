import pytest

from app.core.settings import Settings
from app.rag.ingestion.embeddings import EmbeddingService
from app.rag.providers.in_memory_rag import InMemoryRagProvider


@pytest.mark.asyncio
async def test_in_memory_rag_retrieval(tmp_path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "k8s.txt").write_text(
        "Kubernetes orchestrates containers and schedules pods.", encoding="utf-8"
    )
    (docs_dir / "other.txt").write_text("Redis stores key value data.", encoding="utf-8")
    settings = Settings(rag_docs_path=str(docs_dir), rag_top_k=1)
    provider = InMemoryRagProvider(settings, EmbeddingService(settings))
    await provider.start()
    results = await provider.retrieve("What orchestrates containers?")
    assert results[0].source == "k8s.txt"
