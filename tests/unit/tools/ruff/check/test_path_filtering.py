"""Tests for path filtering in execute_ruff_check."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.tools.implementations.ruff.check import execute_ruff_check


def test_execute_ruff_check_filters_python_files(
    mock_ruff_tool: MagicMock,
) -> None:
    """Filter files to only Python files.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py", "module.pyi"],
        ) as mock_walk,
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        mock_walk.assert_called_once()
        call_kwargs = mock_walk.call_args.kwargs
        assert_that(call_kwargs["file_patterns"]).contains("*.py", "*.pyi")


def test_execute_ruff_check_uses_exclude_patterns(
    mock_ruff_tool: MagicMock,
) -> None:
    """Pass exclude patterns to file walker.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool.exclude_patterns = ["*_test.py", "__pycache__"]

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["main.py"],
        ) as mock_walk,
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        call_kwargs = mock_walk.call_args.kwargs
        assert_that(call_kwargs["exclude_patterns"]).contains(
            "*_test.py",
            "__pycache__",
        )


def test_execute_ruff_check_respects_include_venv(
    mock_ruff_tool: MagicMock,
) -> None:
    """Pass include_venv setting to file walker.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool.include_venv = True

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py"],
        ) as mock_walk,
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        call_kwargs = mock_walk.call_args.kwargs
        assert_that(call_kwargs["include_venv"]).is_true()


def test_execute_ruff_check_converts_paths_to_relative(
    mock_ruff_tool: MagicMock,
) -> None:
    """Convert absolute file paths to relative paths for ruff command.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool._get_cwd.return_value = "/test/project"

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=[
                "/test/project/src/main.py",
                "/test/project/tests/test_main.py",
            ],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch(
            "lintro.tools.implementations.ruff.commands.build_ruff_check_command",
        ) as mock_build_cmd,
    ):
        mock_build_cmd.return_value = [
            "ruff",
            "check",
            "src/main.py",
            "tests/test_main.py",
        ]

        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        call_args = mock_build_cmd.call_args
        files_arg = call_args.kwargs.get("files") or call_args.args[1]
        # Files should be relative paths
        assert_that(files_arg).contains("src/main.py")
        assert_that(files_arg).contains("tests/test_main.py")


def test_execute_ruff_check_handles_multiple_directories(
    mock_ruff_tool: MagicMock,
) -> None:
    """Handle files from multiple directories.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool._get_cwd.return_value = "/test"

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["/test/project1/main.py", "/test/project2/main.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
    ):
        result = execute_ruff_check(mock_ruff_tool, ["/test"])

        assert_that(result.success).is_true()


def test_execute_ruff_check_uses_absolute_paths_when_no_cwd(
    mock_ruff_tool: MagicMock,
) -> None:
    """Use absolute paths when cwd cannot be determined.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool._get_cwd.return_value = None

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["/test/project/test.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(True, "[]"),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch(
            "lintro.tools.implementations.ruff.commands.build_ruff_check_command",
        ) as mock_build_cmd,
    ):
        mock_build_cmd.return_value = ["ruff", "check", "/test/project/test.py"]

        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        call_args = mock_build_cmd.call_args
        files_arg = call_args.kwargs.get("files") or call_args.args[1]
        # Should use absolute path
        assert_that(files_arg[0]).starts_with("/")
