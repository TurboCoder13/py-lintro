"""Shared fixtures for pytest tool tests."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from lintro.tools.implementations.tool_pytest import PytestTool


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


@contextmanager
def patch_pytest_tool_for_check(
    tool: PytestTool,
    *,
    run_subprocess_return: tuple[bool, str] = (True, "All tests passed"),
    prepare_execution_return: tuple[int, int, Any] = (10, 0, None),
) -> Generator[None]:
    """Context manager providing common patches for pytest check tests.

    Args:
        tool: PytestTool instance to patch.
        run_subprocess_return: Return value for _run_subprocess.
        prepare_execution_return: Return value for prepare_test_execution.

    Yields:
        None
    """
    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(tool, "_run_subprocess", return_value=run_subprocess_return),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=prepare_execution_return,
        ),
    ):
        yield
