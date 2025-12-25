"""Integration tests for Clippy Rust linter."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from loguru import logger

from lintro.tools.implementations.tool_clippy import ClippyTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_VIOLATIONS_DIR = Path("test_samples/clippy_violations")
SAMPLE_CLEAN_DIR = Path("test_samples/clippy_clean")


def cargo_clippy_available() -> bool:
    """Check if cargo clippy is available.

    Returns:
        bool: True if cargo clippy is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["cargo", "clippy", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_clippy_directly(project_dir: Path) -> tuple[bool, str, int]:
    """Run cargo clippy directly on a project and return result tuple.

    Args:
        project_dir: Path to the Rust project directory (containing Cargo.toml).

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    cmd = [
        "cargo",
        "clippy",
        "--all-targets",
        "--all-features",
        "--message-format=json",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=60,
        )
        output = result.stdout + result.stderr
        # Count Clippy warnings (lines with "clippy::" in JSON)
        issues_count = sum(
            1
            for line in output.splitlines()
            if '"clippy::' in line and '"reason":"compiler-message"' in line
        )
        # Success is only when there are no issues (regardless of returncode)
        success = issues_count == 0
        return success, output, issues_count
    except subprocess.TimeoutExpired:
        return False, "Timeout", 0
    except Exception as e:
        return False, str(e), 0


@pytest.fixture
def clippy_tool():
    """Create a ClippyTool instance for testing.

    Returns:
        ClippyTool: A configured ClippyTool instance.
    """
    return ClippyTool()


@pytest.fixture
def temp_clippy_violations_project():
    """Copy the clippy_violations sample to a temp directory for testing.

    Yields:
        Path: Path to the temporary project directory.
    """
    src = Path(SAMPLE_VIOLATIONS_DIR).resolve()
    if not src.exists():
        pytest.skip(f"Sample directory {src} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "clippy_violations"
        shutil.copytree(src, dst)
        yield dst


@pytest.fixture
def temp_clippy_clean_project():
    """Copy the clippy_clean sample to a temp directory for testing.

    Yields:
        Path: Path to the temporary project directory.
    """
    src = Path(SAMPLE_CLEAN_DIR).resolve()
    if not src.exists():
        pytest.skip(f"Sample directory {src} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "clippy_clean"
        shutil.copytree(src, dst)
        yield dst
