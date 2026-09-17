from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def clone_repo(github_url: str, max_size_mb: int = 50) -> str:
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    try:
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', github_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError('git clone timed out after 60 seconds.') from None
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    if result.returncode != 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        stderr = (result.stderr or '').strip()
        raise RuntimeError(stderr or 'git clone failed.')

    total_size_bytes = 0
    for root, _, files in os.walk(temp_path):
        for file_name in files:
            file_path = Path(root) / file_name
            total_size_bytes += file_path.stat().st_size

    total_size_mb = total_size_bytes / (1024 * 1024)
    if total_size_mb > max_size_mb:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(
            f'Repository size {total_size_mb:.2f} MB exceeds the limit of {max_size_mb} MB.'
        )

    return str(temp_path.resolve())
