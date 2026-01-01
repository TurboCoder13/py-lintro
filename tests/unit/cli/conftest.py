"""Shared fixtures for CLI unit tests."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner


@pytest.fixture
def mock_tool_manager():
    """Provide a mock tool manager for CLI tests.

    Returns:
        MagicMock: Mock tool manager instance.
    """
    mock_manager = MagicMock()
    mock_manager.get_available_tools.return_value = ["ruff", "yamllint", "prettier"]
    mock_manager.run_tools.return_value = []
    return mock_manager


@pytest.fixture
def mock_format_output():
    """Provide a mock format output function.

    Returns:
        MagicMock: Mock format output function.
    """
    return MagicMock(return_value="formatted output")


@pytest.fixture
def mock_print_summary():
    """Provide a mock print summary function.

    Returns:
        MagicMock: Mock print summary function.
    """
    return MagicMock()


@pytest.fixture
def cli_runner():
    """Provide a Click CLI runner for testing.

    Returns:
        CliRunner: Click CLI test runner instance.
    """
    return CliRunner()
