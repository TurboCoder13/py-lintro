"""Shared timeout handling utilities for tool implementations.

This module provides standardized timeout handling across different tools,
ensuring consistent behavior and error messages for subprocess timeouts.
"""

import subprocess  # nosec B404 - used safely with shell disabled
from typing import Any

from loguru import logger


def run_subprocess_with_timeout(
    tool,
    cmd: list[str],
    timeout: int | None = None,
    cwd: str | None = None,
    tool_name: str | None = None,
) -> tuple[bool, str]:
    """Run a subprocess command with timeout handling.

    This is a wrapper around tool._run_subprocess that provides consistent
    timeout error handling and messaging across different tools.

    Args:
        tool: Tool instance with _run_subprocess method.
        cmd: Command to run.
        timeout: Timeout in seconds. If None, uses tool's default timeout.
        cwd: Working directory for command execution.
        tool_name: Name of the tool for error messages. If None, uses tool.name.

    Returns:
        tuple[bool, str]: (success, output) where success is True if command
        succeeded without timeout, and output contains command output or
        timeout error message.

    Raises:
        TimeoutExpired: If command times out (re-raised from subprocess).
    """
    tool_name = tool_name or tool.name

    try:
        return tool._run_subprocess(cmd=cmd, timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired as e:
        # Re-raise with more context for the calling tool
        actual_timeout = timeout or tool.options.get("timeout", tool._default_timeout)
        timeout_msg = (
            f"{tool_name} execution timed out ({actual_timeout}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options timeout=N\n"
            "  - Command hanging due to external dependencies\n"
        )
        logger.warning(timeout_msg)

        # Create a new TimeoutExpired with enhanced message
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=actual_timeout,
            output=timeout_msg,
        ) from e


def get_timeout_value(tool, default_timeout: int | None = None) -> int:
    """Get timeout value from tool options with fallback to default.

    Args:
        tool: Tool instance with options.
        default_timeout: Default timeout if not specified in options.

    Returns:
        int: Timeout value in seconds.
    """
    if default_timeout is None:
        default_timeout = getattr(tool, "_default_timeout", 300)

    return tool.options.get("timeout", default_timeout)


def create_timeout_result(
    tool,
    timeout: int,
    cmd: list[str] | None = None,
    tool_name: str | None = None,
) -> dict[str, Any]:
    """Create a standardized timeout result dictionary.

    Args:
        tool: Tool instance.
        timeout: Timeout value that was exceeded.
        cmd: Optional command that timed out.
        tool_name: Optional tool name override.

    Returns:
        dict: Result dictionary with timeout information.
    """
    tool_name = tool_name or tool.name

    return {
        "success": False,
        "output": (
            f"{tool_name} execution timed out ({timeout}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options timeout=N\n"
            "  - Command hanging due to external dependencies\n"
        ),
        "issues_count": 1,  # Count timeout as execution failure
        "issues": [],
        "timed_out": True,
        "timeout_seconds": timeout,
    }
