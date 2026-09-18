from __future__ import annotations

import shutil
import subprocess
import tempfile
import sys
from pathlib import Path


def apply_patch_and_run_test(
    repo_path: str,
    target_file: str,
    original_code: str,
    new_code: str,
    test_code: str,
    timeout_seconds: int = 30,
) -> dict:
    temp_dir = tempfile.mkdtemp()
    temp_repo_path = Path(temp_dir) / "repo_copy"

    try:
        shutil.copytree(repo_path, temp_repo_path, dirs_exist_ok=True)

        target_path = Path(temp_repo_path) / target_file
        file_content = target_path.read_text(encoding="utf-8")

        if original_code not in file_content:
            return {
                "applied": False,
                "passed": False,
                "stdout": "",
                "stderr": "",
                "reason": "original_code not found verbatim in target file; patch not applied",
            }

        updated_content = file_content.replace(original_code, new_code, 1)
        target_path.write_text(updated_content, encoding="utf-8")

        test_path = Path(temp_repo_path) / "test_generated.py"
        test_path.write_text(test_code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "test_generated.py", "-v"],
                cwd=temp_repo_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {
                "applied": True,
                "passed": False,
                "stdout": "",
                "stderr": "",
                "reason": f"Test execution timed out after {timeout_seconds} seconds",
            }

        passed = result.returncode == 0
        return {
            "applied": True,
            "passed": passed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "reason": None,
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
