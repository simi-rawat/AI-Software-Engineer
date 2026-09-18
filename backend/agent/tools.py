from __future__ import annotations

from pathlib import Path

from backend.retrieval.vector_store import query_similar


def search_code(query: str, k: int = 5) -> list[dict]:
    return query_similar(query, k=k)


def read_file(relative_path: str, repo_path: str) -> str:
    repo_root = Path(repo_path).resolve()
    full_path = (Path(repo_path) / relative_path).resolve()

    is_safe_path = False
    if hasattr(full_path, "is_relative_to"):
        try:
            is_safe_path = full_path.is_relative_to(repo_root)
        except Exception:
            is_safe_path = False
    else:
        is_safe_path = str(full_path).startswith(str(repo_root))

    if not is_safe_path:
        raise ValueError("Path traversal detected: refusing to read outside repository root.")

    try:
        return full_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return f"Error: could not read file at {relative_path}"
