"""Tests for the extract-version utility script."""

from __future__ import annotations

import subprocess
from pathlib import Path

from assertpy import assert_that


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command and capture output for assertions.

    Args:
        cmd: Command and arguments to execute.
        cwd: Working directory for the command.

    Returns:
        CompletedProcess[str]: Completed process with stdout/stderr.
    """
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def test_extract_version_from_repo_root(tmp_path: Path) -> None:
    """Extract version with default file from repo root copy.

    Args:
        tmp_path: Temporary directory provided by pytest.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "pyproject.toml"
    dst = tmp_path / "pyproject.toml"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    script = repo_root / "scripts" / "utils" / "extract-version.py"
    result = run(["python", str(script)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert_that(result.stdout.startswith("version=")).is_true()
    assert_that(len(result.stdout.strip().split("=", 1)[1]) > 0).is_true()


def test_extract_version_with_custom_file(tmp_path: Path) -> None:
    """Extract version when a custom TOML file is provided.

    Args:
        tmp_path: Temporary directory provided by pytest.
    """
    toml = tmp_path / "custom.toml"
    toml.write_text('\n[project]\nversion = "9.9.9"\n'.strip(), encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "utils" / "extract-version.py"
    result = run(["python", str(script), "--file", str(toml)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert_that(result.stdout.strip()).is_equal_to("version=9.9.9")
