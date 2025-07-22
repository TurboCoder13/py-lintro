"""Shared test fixtures and configuration for all tests.

This module provides shared fixtures and configuration for all test modules in Lintro.
"""

import pytest
from click.testing import CliRunner
import tempfile
from pathlib import Path


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
        Path: Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def clear_logging_handlers():
    """Clear logging handlers before each test.

    Yields:
        None: This fixture is used for its side effect only.
    """
    import logging

    logging.getLogger().handlers.clear()
    yield
