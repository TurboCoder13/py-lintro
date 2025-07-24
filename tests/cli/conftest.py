"""Test fixtures for CLI tests.

This module provides shared fixtures for testing CLI utilities in Lintro.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tool_manager():
    """Provide a mock tool manager for CLI tests.

    Returns:
        MagicMock: Mocked tool manager object.
    """
    mock_manager = MagicMock()
    mock_manager.get_available_tools.return_value = ["ruff", "yamllint", "prettier"]
    mock_manager.run_tools.return_value = []
    return mock_manager


@pytest.fixture
def mock_format_output():
    """Provide a mock format output function.

    Returns:
        MagicMock: Mocked format output function.
    """
    return MagicMock(return_value="formatted output")


@pytest.fixture
def mock_print_summary():
    """Provide a mock print summary function.

    Returns:
        MagicMock: Mocked print summary function.
    """
    return MagicMock()
