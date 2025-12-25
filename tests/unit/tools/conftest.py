"""Shared fixtures for tool unit tests."""

from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for tool testing.

    Yields:
        Mock: Configured mock for subprocess operations.
    """
    with patch("subprocess.run") as mock_run:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_tool_config():
    """Provide a mock tool configuration.

    Returns:
        dict: Sample tool configuration dictionary.
    """
    return {
        "priority": 50,
        "file_patterns": ["*.py"],
        "tool_type": "linter",
        "options": {
            "timeout": 30,
            "line_length": 88,
        },
    }


@pytest.fixture
def mock_tool_result():
    """Provide a mock tool result.

    Returns:
        Mock: Configured mock tool result with default values.
    """
    result = Mock()
    result.name = "test_tool"
    result.success = True
    result.output = ""
    result.issues_count = 0
    result.issues = []
    return result
