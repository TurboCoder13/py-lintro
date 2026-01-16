"""Unit tests for taplo plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.taplo.taplo_parser import parse_taplo_output
from lintro.tools.definitions.taplo import (
    TAPLO_DEFAULT_TIMEOUT,
    TaploPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def taplo_plugin() -> TaploPlugin:
    """Provide a TaploPlugin instance for testing.

    Returns:
        A TaploPlugin instance with mocked version verification.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return TaploPlugin()


# Tests for TaploPlugin default options


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", TAPLO_DEFAULT_TIMEOUT),
        ("schema", None),
        ("aligned_arrays", None),
        ("aligned_entries", None),
        ("array_trailing_comma", None),
        ("indent_string", None),
        ("reorder_keys", None),
    ],
    ids=[
        "timeout_equals_default",
        "schema_is_none",
        "aligned_arrays_is_none",
        "aligned_entries_is_none",
        "array_trailing_comma_is_none",
        "indent_string_is_none",
        "reorder_keys_is_none",
    ],
)
def test_default_options_values(
    taplo_plugin: TaploPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        taplo_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for TaploPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("schema", "/path/to/schema.json"),
        ("aligned_arrays", True),
        ("aligned_entries", True),
        ("array_trailing_comma", True),
        ("indent_string", "    "),
        ("indent_string", "\t"),
        ("reorder_keys", True),
        ("reorder_keys", False),
    ],
    ids=[
        "schema_path",
        "aligned_arrays_true",
        "aligned_entries_true",
        "array_trailing_comma_true",
        "indent_string_spaces",
        "indent_string_tab",
        "reorder_keys_true",
        "reorder_keys_false",
    ],
)
def test_set_options_valid(
    taplo_plugin: TaploPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    taplo_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(taplo_plugin.options.get(option_name)).is_equal_to(option_value)


# Tests for TaploPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("schema", 123, "schema must be a string"),
        ("schema", ["path"], "schema must be a string"),
        ("aligned_arrays", "yes", "aligned_arrays must be a boolean"),
        ("aligned_arrays", 1, "aligned_arrays must be a boolean"),
        ("aligned_entries", "true", "aligned_entries must be a boolean"),
        ("array_trailing_comma", 0, "array_trailing_comma must be a boolean"),
        ("indent_string", 4, "indent_string must be a string"),
        ("indent_string", True, "indent_string must be a string"),
        ("reorder_keys", "yes", "reorder_keys must be a boolean"),
    ],
    ids=[
        "invalid_schema_int",
        "invalid_schema_list",
        "invalid_aligned_arrays_str",
        "invalid_aligned_arrays_int",
        "invalid_aligned_entries_str",
        "invalid_array_trailing_comma_int",
        "invalid_indent_string_int",
        "invalid_indent_string_bool",
        "invalid_reorder_keys_str",
    ],
)
def test_set_options_invalid_type(
    taplo_plugin: TaploPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        taplo_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for TaploPlugin._build_format_args method


def test_build_format_args_no_options(taplo_plugin: TaploPlugin) -> None:
    """Build format args returns empty list when no options set.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    args = taplo_plugin._build_format_args()
    assert_that(args).is_empty()


def test_build_format_args_with_aligned_arrays(taplo_plugin: TaploPlugin) -> None:
    """Build format args includes aligned_arrays option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(aligned_arrays=True)
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=aligned_arrays=true")


def test_build_format_args_with_aligned_entries(taplo_plugin: TaploPlugin) -> None:
    """Build format args includes aligned_entries option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(aligned_entries=True)
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=aligned_entries=true")


def test_build_format_args_with_array_trailing_comma(
    taplo_plugin: TaploPlugin,
) -> None:
    """Build format args includes array_trailing_comma option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(array_trailing_comma=True)
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=array_trailing_comma=true")


def test_build_format_args_with_indent_string(taplo_plugin: TaploPlugin) -> None:
    """Build format args includes indent_string option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(indent_string="    ")
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=indent_string=    ")


def test_build_format_args_with_reorder_keys(taplo_plugin: TaploPlugin) -> None:
    """Build format args includes reorder_keys option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(reorder_keys=True)
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=reorder_keys=true")


def test_build_format_args_with_all_options(taplo_plugin: TaploPlugin) -> None:
    """Build format args includes all formatting options.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(
        aligned_arrays=True,
        aligned_entries=True,
        array_trailing_comma=True,
        indent_string="\t",
        reorder_keys=True,
    )
    args = taplo_plugin._build_format_args()

    assert_that(args).contains("--option=aligned_arrays=true")
    assert_that(args).contains("--option=aligned_entries=true")
    assert_that(args).contains("--option=array_trailing_comma=true")
    assert_that(args).contains("--option=indent_string=\t")
    assert_that(args).contains("--option=reorder_keys=true")
    assert_that(args).is_length(5)


# Tests for TaploPlugin._build_lint_args method


def test_build_lint_args_no_options(taplo_plugin: TaploPlugin) -> None:
    """Build lint args returns empty list when no options set.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    args = taplo_plugin._build_lint_args()
    assert_that(args).is_empty()


def test_build_lint_args_with_schema(taplo_plugin: TaploPlugin) -> None:
    """Build lint args includes schema option.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    taplo_plugin.set_options(schema="/path/to/schema.json")
    args = taplo_plugin._build_lint_args()

    assert_that(args).contains("--schema")
    schema_idx = args.index("--schema")
    assert_that(args[schema_idx + 1]).is_equal_to("/path/to/schema.json")


def test_build_lint_args_with_url_schema(taplo_plugin: TaploPlugin) -> None:
    """Build lint args includes schema URL.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
    """
    schema_url = "https://json.schemastore.org/pyproject.json"
    taplo_plugin.set_options(schema=schema_url)
    args = taplo_plugin._build_lint_args()

    assert_that(args).contains("--schema")
    schema_idx = args.index("--schema")
    assert_that(args[schema_idx + 1]).is_equal_to(schema_url)


# Tests for TaploPlugin.check method


def test_check_with_mocked_subprocess_success(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no issues found.

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
            return_value=(True, ""),
        ):
            result = taplo_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_lint_errors(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when taplo lint finds problems.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text("invalid = \n")

    taplo_output = """error[invalid_value]: invalid value
  --> test.toml:1:10
   |
 1 | invalid =
   |          ^ expected a value
"""

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            taplo_plugin,
            "_run_subprocess",
            side_effect=[(False, taplo_output), (True, "")],
        ):
            result = taplo_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


def test_check_with_mocked_subprocess_format_issues(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when taplo fmt --check finds formatting problems.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname="test"\n')

    format_output = """error[formatting]: the file is not properly formatted
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
            side_effect=[(True, ""), (False, format_output)],
        ):
            result = taplo_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


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


def test_check_with_no_toml_files(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no TOML files found.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_toml_file = tmp_path / "test.txt"
    non_toml_file.write_text("Not a TOML file")

    with patch.object(taplo_plugin, "_verify_tool_version", return_value=None):
        result = taplo_plugin.check([str(non_toml_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No")


# Tests for TaploPlugin.fix method


def test_fix_with_mocked_subprocess_success(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when formatting applied successfully.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text('[project]\nname="test"\n')

    format_issue_output = """error[formatting]: the file is not properly formatted
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
                (False, format_issue_output),  # initial format check
                (True, ""),  # lint check
                (True, ""),  # fix command
                (True, ""),  # final format check
                (True, ""),  # final lint check
            ],
        ):
            result = taplo_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.fixed_issues_count).is_equal_to(1)
    assert_that(result.remaining_issues_count).is_equal_to(0)


def test_fix_with_mocked_subprocess_partial_fix(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns partial success when some issues cannot be fixed.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test.toml"
    test_file.write_text("invalid = \n")

    format_issue = """error[formatting]: the file is not properly formatted
  --> test.toml:1:1
   |
 1 | invalid =
   | ^ formatting issue
"""
    lint_issue = """error[invalid_value]: invalid value
  --> test.toml:1:10
   |
 1 | invalid =
   |          ^ expected a value
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
                (False, lint_issue),  # initial lint check
                (True, ""),  # fix command
                (True, ""),  # final format check - format is fixed
                (False, lint_issue),  # final lint check - syntax error remains
            ],
        ):
            result = taplo_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.initial_issues_count).is_equal_to(2)
    assert_that(result.fixed_issues_count).is_equal_to(1)
    assert_that(result.remaining_issues_count).is_equal_to(1)


def test_fix_with_no_changes_needed(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when no changes are needed.

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
                (True, ""),  # initial format check - no issues
                (True, ""),  # initial lint check - no issues
                (True, ""),  # fix command
                (True, ""),  # final format check
                (True, ""),  # final lint check
            ],
        ):
            result = taplo_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.initial_issues_count).is_equal_to(0)
    assert_that(result.fixed_issues_count).is_equal_to(0)
    assert_that(result.remaining_issues_count).is_equal_to(0)


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


def test_fix_with_no_toml_files(
    taplo_plugin: TaploPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when no TOML files found.

    Args:
        taplo_plugin: The TaploPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_toml_file = tmp_path / "test.txt"
    non_toml_file.write_text("Not a TOML file")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        result = taplo_plugin.fix([str(non_toml_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No .toml files")


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
