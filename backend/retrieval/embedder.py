from __future__ import annotations

from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    return MODEL.encode(text).tolist()
