"""Pytest configuration for gitleaks integration tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


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
GITLEAKS_SAMPLES = SAMPLE_DIR / "tools" / "security" / "gitleaks"
CLEAN_SAMPLE = GITLEAKS_SAMPLES / "gitleaks_clean.py"
VIOLATION_SAMPLE = GITLEAKS_SAMPLES / "gitleaks_violations.py"


@pytest.fixture
def gitleaks_violation_file(tmp_path: Path) -> str:
    """Copy the gitleaks violation sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "gitleaks_violations.py"
    shutil.copy(VIOLATION_SAMPLE, dst)
    return str(dst)


@pytest.fixture
def gitleaks_clean_file(tmp_path: Path) -> str:
    """Copy the gitleaks clean sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "gitleaks_clean.py"
    shutil.copy(CLEAN_SAMPLE, dst)
    return str(dst)
