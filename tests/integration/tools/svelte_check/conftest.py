"""Pytest configuration for svelte-check integration tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def svelte_check_is_available() -> bool:
    """Check if svelte-check is installed and actually works.

    This checks both that the command exists AND that it executes successfully,
    which handles cases where a wrapper script exists but the underlying
    tool isn't installed. Also checks bunx/npx fallbacks.

    Returns:
        True if svelte-check is installed and working, False otherwise.
    """
    # Try direct svelte-check command first
    if shutil.which("svelte-check") is not None:
        try:
            result = subprocess.run(
                ["svelte-check", "--version"],
                capture_output=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Try bunx fallback
    if shutil.which("bunx") is not None:
        try:
            result = subprocess.run(
                ["bunx", "svelte-check", "--version"],
                capture_output=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Try npx fallback
    if shutil.which("npx") is not None:
        try:
            result = subprocess.run(
                ["npx", "svelte-check", "--version"],
                capture_output=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, OSError):
            pass

    return False


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml.

    Returns:
        Path to the project root directory.

    Raises:
        RuntimeError: If pyproject.toml is not found in any parent directory.
    """
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("pyproject.toml not found in parent directories")


# Paths to test samples
SAMPLE_DIR = _find_project_root() / "test_samples"
SVELTE_CHECK_SAMPLES = SAMPLE_DIR / "tools" / "web" / "svelte_check"
CLEAN_SAMPLE = SVELTE_CHECK_SAMPLES / "svelte_check_clean.svelte"
VIOLATION_SAMPLE = SVELTE_CHECK_SAMPLES / "svelte_check_violations.svelte"


@pytest.fixture
def svelte_check_violation_file(tmp_path: Path) -> str:
    """Copy the svelte-check violation sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "svelte_check_violations.svelte"
    shutil.copy(VIOLATION_SAMPLE, dst)
    return str(dst)


@pytest.fixture
def svelte_check_clean_file(tmp_path: Path) -> str:
    """Copy the svelte-check clean sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "svelte_check_clean.svelte"
    shutil.copy(CLEAN_SAMPLE, dst)
    return str(dst)
