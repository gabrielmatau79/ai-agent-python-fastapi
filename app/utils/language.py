from __future__ import annotations

import re
from collections import Counter

SPANISH_MARKERS = {"hola", "gracias", "que", "qué", "para", "porque", "como", "cómo", "usted"}
FRENCH_MARKERS = {"bonjour", "merci", "pourquoi", "avec", "vous", "être", "été"}
PORTUGUESE_MARKERS = {"olá", "obrigado", "você", "não", "como", "para"}


def detect_language(text: str, default: str = "en") -> str:
    content = text.strip().lower()
    if not content:
        return default
    tokens = re.findall(r"[a-zA-ZÀ-ÿ']+", content)
    if not tokens:
        return default

    score = Counter[str]()
    if any(token in SPANISH_MARKERS for token in tokens) or any(ch in content for ch in "¿¡ñ"):
        score["es"] += 3
    if any(token in FRENCH_MARKERS for token in tokens):
        score["fr"] += 3
    if any(token in PORTUGUESE_MARKERS for token in tokens) or "ção" in content:
        score["pt"] += 3
    if re.search(r"\b(the|what|when|where|how|is|are|can|you)\b", content):
        score["en"] += 2
    if re.search(r"\b(el|la|los|las|una|uno|puede|explica)\b", content):
        score["es"] += 2

    if not score:
        return default
    language, confidence = score.most_common(1)[0]
    return language if confidence >= 2 else default
