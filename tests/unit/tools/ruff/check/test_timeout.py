"""Tests for timeout configuration in execute_ruff_check."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.tools.implementations.ruff.check import (
    RUFF_DEFAULT_TIMEOUT,
    execute_ruff_check,
)


def test_execute_ruff_check_uses_default_timeout() -> None:
    """Verify default timeout constant is set correctly."""
    assert_that(RUFF_DEFAULT_TIMEOUT).is_equal_to(30)


def test_execute_ruff_check_uses_tool_timeout(
    mock_ruff_tool: MagicMock,
) -> None:
    """Use timeout from tool options.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool.options["timeout"] = 60

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ) as mock_subprocess,
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.get_timeout_value",
            return_value=60,
        ),
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        call_kwargs = mock_subprocess.call_args.kwargs
        assert_that(call_kwargs.get("timeout")).is_equal_to(60)
