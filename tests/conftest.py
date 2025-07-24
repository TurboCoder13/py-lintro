"""Shared test fixtures and configuration for all tests.

This module provides shared fixtures and configuration for all test modules in Lintro.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from lintro.utils.path_utils import normalize_file_path_for_display


@pytest.fixture
def cli_runner():
    """Provide a Click CLI runner for testing.

    Returns:
        click.testing.CliRunner: CLI runner for invoking commands.
    """
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing.

    Yields:
        temp_dir (Path): Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def ruff_violation_file(temp_dir):
    """Copy the ruff_violations.py sample to a temp directory for testing and return normalized path.

    Args:
        temp_dir (Path): Temporary directory fixture.

    Returns:
        str: Normalized path to the copied ruff_violations.py file.
    """
    src = Path("test_samples/ruff_violations.py").resolve()
    dst = temp_dir / "ruff_violations.py"
    shutil.copy(src, dst)
    return normalize_file_path_for_display(str(dst))


@pytest.fixture(autouse=True)
def clear_logging_handlers():
    """Clear logging handlers before each test.

    Yields:
        None: This fixture is used for its side effect only.
    """
    import logging

    logging.getLogger().handlers.clear()
    yield
