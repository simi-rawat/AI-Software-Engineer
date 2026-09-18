from __future__ import annotations

from pathlib import Path

from backend.retrieval.vector_store import query_similar


def search_code(query: str, k: int = 5) -> list[dict]:
    """Search the indexed repository for code chunks semantically relevant to the query text.

    Returns a list of matching code chunks with their file path, qualified name,
    source code, and similarity metadata.

    Args:
        query: A natural language description of what code to find.
        k: Number of top results to return.
    """
    return query_similar(query, k=k)


def read_file(relative_path: str, repo_path: str) -> str:
    """Read the full contents of a specific file in the repository.

    Use this when a code chunk alone does not give enough context and you need to
    inspect the complete file.

    Args:
        relative_path: Path to the file relative to the repository root.
        repo_path: The root path of the repository being investigated.
    """
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
