"""Tests for TaploPlugin error handling, timeouts, and edge cases."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from lintro.parsers.taplo.taplo_parser import parse_taplo_output
from lintro.tools.definitions.taplo import TaploPlugin

# Tests for timeout handling in check method


def test_check_with_timeout(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname = "test"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            taplo_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["taplo"], timeout=30),
        ):
            result = taplo_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)
    assert_that(result.output).contains("timed out")


def test_check_with_timeout_on_format_check(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout during format check correctly.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname = "test"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            taplo_plugin,
            "_run_subprocess",
            side_effect=[
                (True, ""),  # lint succeeds
                subprocess.TimeoutExpired(cmd=["taplo"], timeout=30),  # fmt times out
            ],
        ):
            result = taplo_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")


# Tests for timeout handling in fix method


def test_fix_with_timeout(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix handles timeout correctly.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname = "test"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            taplo_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["taplo"], timeout=30),
        ):
            result = taplo_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")


def test_fix_with_timeout_during_fix_command(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix handles timeout during fix command correctly.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname="test"\n')

    format_issue = """error[formatting]: the file is not properly formatted
  --> test.toml:2:1
   |
 2 | name="test"
   | ^ formatting issue
"""

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            taplo_plugin,
            "_run_subprocess",
            side_effect=[
                (False, format_issue),  # initial format check
                (True, ""),  # initial lint check
                subprocess.TimeoutExpired(cmd=["taplo"], timeout=30),  # fix times out
            ],
        ):
            result = taplo_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")
    assert_that(result.initial_issues_count).is_equal_to(1)


# Tests for output parsing integration


def test_parse_taplo_output_single_issue() -> None:
    """Parse single issue from taplo output."""
    output = """error[invalid_value]: invalid value
  --> test.toml:5:10
   |
 5 | version =
   |          ^ expected a value
"""
    issues = parse_taplo_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.toml")
    assert_that(issues[0].line).is_equal_to(5)
    assert_that(issues[0].column).is_equal_to(10)
    assert_that(issues[0].code).is_equal_to("invalid_value")
    assert_that(issues[0].message).is_equal_to("invalid value")


def test_parse_taplo_output_multiple_issues() -> None:
    """Parse multiple issues from taplo output."""
    output = """error[invalid_value]: first error
  --> test.toml:1:5
   |
 1 | key =
   |     ^ expected a value

warning[deprecated]: deprecated feature
  --> test.toml:10:1
   |
10 | old_key = "value"
   | ^ deprecated
"""
    issues = parse_taplo_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].level).is_equal_to("error")
    assert_that(issues[0].code).is_equal_to("invalid_value")
    assert_that(issues[1].level).is_equal_to("warning")
    assert_that(issues[1].code).is_equal_to("deprecated")


def test_parse_taplo_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_taplo_output("")

    assert_that(issues).is_empty()


def test_parse_taplo_output_none() -> None:
    """Parse None output returns empty list."""
    issues = parse_taplo_output(None)

    assert_that(issues).is_empty()
