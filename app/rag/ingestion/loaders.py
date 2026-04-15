from __future__ import annotations

import csv
from pathlib import Path

from pypdf import PdfReader

from app.rag.models import SourceDocument

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".pdf"}


def load_documents(path: Path) -> list[SourceDocument]:
    path.mkdir(parents=True, exist_ok=True)
    documents: list[SourceDocument] = []
    for file_path in sorted(path.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if file_path.suffix.lower() in {".txt", ".md"}:
            documents.append(
                SourceDocument(source=file_path.name, content=file_path.read_text(encoding="utf-8"))
            )
        elif file_path.suffix.lower() == ".csv":
            rows: list[str] = []
            with file_path.open("r", encoding="utf-8", newline="") as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    rows.append(", ".join(cell.strip() for cell in row))
            documents.append(SourceDocument(source=file_path.name, content="\n".join(rows)))
        elif file_path.suffix.lower() == ".pdf":
            pdf_reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in pdf_reader.pages]
            documents.append(SourceDocument(source=file_path.name, content="\n".join(pages)))
    if not documents:
        sample = path / "example.txt"
        sample.write_text(
            "RAG sample document. Retrieval augmented generation combines model reasoning "
            "with relevant documents.",
            encoding="utf-8",
        )
        documents.append(
            SourceDocument(source=sample.name, content=sample.read_text(encoding="utf-8"))
        )
    return documents
