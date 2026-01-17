"""Pytest configuration for gitleaks integration tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# Paths to test samples
SAMPLE_DIR = Path(__file__).parent.parent.parent.parent.parent / "test_samples"
GITLEAKS_SAMPLES = SAMPLE_DIR / "tools" / "security" / "gitleaks"
VIOLATIONS_SAMPLE = GITLEAKS_SAMPLES / "gitleaks_violations.py"
CLEAN_SAMPLE = GITLEAKS_SAMPLES / "gitleaks_clean.py"


@pytest.fixture
def gitleaks_violation_file(tmp_path: Path) -> str:
    """Copy the gitleaks violations sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "gitleaks_violations.py"
    shutil.copy(VIOLATIONS_SAMPLE, dst)
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
