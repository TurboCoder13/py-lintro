"""Shared fixtures for ShellCheck integration tests.

These tests require shellcheck to be installed and available in PATH.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# Path to test samples
SAMPLE_DIR = Path(__file__).parent.parent.parent.parent.parent / "test_samples"
SHELLCHECK_SAMPLES = SAMPLE_DIR / "tools" / "shell" / "shellcheck"

# Validate sample paths exist at import time for clearer error messages
if not SHELLCHECK_SAMPLES.exists():
    raise FileNotFoundError(
        f"ShellCheck test samples not found at: {SHELLCHECK_SAMPLES}",
    )

# Sample file paths
VIOLATIONS_SAMPLE = SHELLCHECK_SAMPLES / "shellcheck_violations.sh"
CLEAN_SAMPLE = SHELLCHECK_SAMPLES / "shellcheck_clean.sh"
STYLE_ISSUES_SAMPLE = SHELLCHECK_SAMPLES / "shellcheck_style_issues.sh"


@pytest.fixture
def shellcheck_violation_file(tmp_path: Path) -> str:
    """Create a temporary copy of the shellcheck violations sample file.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "shellcheck_violations.sh"
    shutil.copy(VIOLATIONS_SAMPLE, dst)
    return str(dst)


@pytest.fixture
def shellcheck_clean_file(tmp_path: Path) -> str:
    """Create a temporary copy of the clean shellcheck sample file.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "shellcheck_clean.sh"
    shutil.copy(CLEAN_SAMPLE, dst)
    return str(dst)


@pytest.fixture
def shellcheck_style_issues_file(tmp_path: Path) -> str:
    """Create a temporary copy of the shellcheck style issues sample file.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "shellcheck_style_issues.sh"
    shutil.copy(STYLE_ISSUES_SAMPLE, dst)
    return str(dst)
