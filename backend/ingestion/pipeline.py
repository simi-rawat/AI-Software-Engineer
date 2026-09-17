from __future__ import annotations

from backend.ingestion.repo_cloner import clone_repo
from backend.ingestion.repo_walker import walk_python_files


def ingest_repository(source: str, is_url: bool | None = None) -> dict:
    if is_url is None:
        is_url = source.lower().startswith(('http://', 'https://'))

    if is_url:
        local_path = clone_repo(source)
        was_cloned = True
    else:
        local_path = source
        was_cloned = False

    files = walk_python_files(local_path)
    return {
        'repo_path': local_path,
        'files': files,
        'was_cloned': was_cloned,
    }
