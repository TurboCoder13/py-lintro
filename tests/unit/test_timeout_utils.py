"""Unit tests for timeout utilities."""

import subprocess
from unittest.mock import Mock

import pytest

from lintro.tools.core.timeout_utils import (
    create_timeout_result,
    get_timeout_value,
    run_subprocess_with_timeout,
)


class MockTool:
    """Mock tool for testing timeout utilities."""

    def __init__(self, name="test_tool", default_timeout=300) -> None:
        """Initialize mock tool.

        Args:
            name: Tool name for testing.
            default_timeout: Default timeout value in seconds.
        """
        self.name = name
        self._default_timeout = default_timeout
        self.options = {}

    def _run_subprocess(self, cmd, timeout=None, cwd=None):
        """Mock subprocess runner.

        Args:
            cmd: Command to run.
            timeout: Optional timeout value.
            cwd: Optional working directory.

        Returns:
            tuple[bool, str]: Success status and output.
        """
        return True, "success"


def test_get_timeout_value_with_option():
    """Test getting timeout value when set in options."""
    tool = MockTool()
    tool.options["timeout"] = 60

    assert get_timeout_value(tool) == 60


def test_get_timeout_value_with_default():
    """Test getting timeout value when using tool default."""
    tool = MockTool(default_timeout=45)

    assert get_timeout_value(tool) == 45


def test_get_timeout_value_with_custom_default():
    """Test getting timeout value with custom default parameter."""
    tool = MockTool()

    assert get_timeout_value(tool, 120) == 120


def test_create_timeout_result():
    """Test creating a timeout result dictionary."""
    tool = MockTool("pytest")

    result = create_timeout_result(tool, 30, ["pytest", "test"])

    assert result["success"] is False
    assert "pytest execution timed out (30s limit exceeded)" in result["output"]
    assert result["issues_count"] == 1
    assert result["issues"] == []
    assert result["timed_out"] is True
    assert result["timeout_seconds"] == 30


def test_run_subprocess_with_timeout_success():
    """Test successful subprocess execution with timeout."""
    tool = MockTool()
    tool._run_subprocess = Mock(return_value=(True, "output"))

    success, output = run_subprocess_with_timeout(tool, ["echo", "test"])

    assert success is True
    assert output == "output"
    tool._run_subprocess.assert_called_once_with(
        cmd=["echo", "test"],
        timeout=None,
        cwd=None,
    )


def test_run_subprocess_with_timeout_exception():
    """Test subprocess timeout exception handling."""
    tool = MockTool()

    # Mock subprocess to raise TimeoutExpired
    def mock_run_subprocess(**kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["slow", "command"],
            timeout=10,
            output="timeout occurred",
        )

    tool._run_subprocess = mock_run_subprocess

    with pytest.raises(subprocess.TimeoutExpired) as exc_info:
        run_subprocess_with_timeout(tool, ["slow", "command"], timeout=10)

    # Verify the exception has enhanced message
    assert "test_tool execution timed out" in str(exc_info.value.output)
    assert "(10s limit exceeded)" in str(exc_info.value.output)
