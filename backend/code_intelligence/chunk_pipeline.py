from __future__ import annotations

from backend.code_intelligence.ast_chunker import extract_chunks


def chunk_repository(files: list[dict]) -> list[dict]:
    chunks: list[dict] = []
    for file in files:
        chunks.extend(extract_chunks(file['absolute_path'], file['path']))
    return chunks
