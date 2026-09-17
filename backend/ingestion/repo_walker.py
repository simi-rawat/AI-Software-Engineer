from __future__ import annotations

import os
from pathlib import Path


def walk_python_files(repo_path: str, max_files: int = 200, max_file_size_kb: int = 500) -> list[dict]:
    repo_root = Path(repo_path).resolve()
    included_files: list[dict] = []
    excluded_parts = {'.git', 'venv', '.venv', '__pycache__', 'node_modules'}

    for current_root, dirnames, filenames in os.walk(repo_root):
        current_path = Path(current_root)
        if any(part in excluded_parts for part in current_path.parts):
            dirnames[:] = []
            continue

        dirnames[:] = [
            directory
            for directory in dirnames
            if directory not in excluded_parts
        ]

        for filename in filenames:
            if not filename.endswith('.py'):
                continue

            file_path = current_path / filename
            if any(part in excluded_parts for part in file_path.parts):
                continue

            file_size_kb = file_path.stat().st_size / 1024
            if file_size_kb > max_file_size_kb:
                continue

            included_files.append(
                {
                    'path': file_path.relative_to(repo_root).as_posix(),
                    'absolute_path': str(file_path.resolve()),
                    'size_kb': round(file_size_kb, 2),
                }
            )
            if len(included_files) > max_files:
                raise ValueError(
                    f"Exceeded max_files limit of {max_files} while walking the repository."
                )

    return included_files
