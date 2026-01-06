"""Shared fixtures for pytest tool tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_pytest_tool() -> MagicMock:
    """Provide a mock PytestTool instance for testing.

    Returns:
        MagicMock: Mock PytestTool instance.
    """
    tool = MagicMock()
    tool.name = "pytest"
    tool.can_fix = False
    tool.options = {}
    tool._default_timeout = 300
    tool.config.priority = 90

    # Mock common methods
    tool._get_executable_command.return_value = ["pytest"]
    tool._verify_tool_version.return_value = None

    return tool
