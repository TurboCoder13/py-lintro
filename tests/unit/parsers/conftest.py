"""Shared fixtures for parser unit tests."""

from __future__ import annotations

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_tool_output() -> Mock:
    """Provide a mock tool output for parser testing.

    Returns:
        Mock: Configured mock with sample tool output data.
    """
    mock_output = Mock()
    mock_output.stdout = ""
    mock_output.stderr = ""
    mock_output.returncode = 0
    return mock_output


@pytest.fixture
def sample_ruff_json_output() -> str:
    """Provide sample JSON output from ruff for testing.

    Returns:
        str: JSON-formatted string mimicking ruff output.
    """
    return """[
        {
            "code": "F401",
            "message": "Unused import",
            "location": {"row": 1, "column": 1},
            "filename": "test.py"
        }
    ]"""


@pytest.fixture
def sample_pytest_json_output() -> str:
    """Provide sample JSON output from pytest for testing.

    Returns:
        str: JSON-formatted string mimicking pytest output.
    """
    return """{
        "session": {
            "tests": 5,
            "passed": 3,
            "failed": 2,
            "errors": 0,
            "warnings": 0
        },
        "tests": [
            {
                "nodeid": "test_example.py::test_pass",
                "outcome": "passed",
                "duration": 0.01
            },
            {
                "nodeid": "test_example.py::test_fail",
                "outcome": "failed",
                "duration": 0.02
            }
        ]
    }"""
