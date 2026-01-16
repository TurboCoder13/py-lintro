"""Unit tests for shfmt plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.shfmt.shfmt_parser import parse_shfmt_output
from lintro.tools.definitions.shfmt import (
    SHFMT_DEFAULT_TIMEOUT,
    ShfmtPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def shfmt_plugin() -> ShfmtPlugin:
    """Provide a ShfmtPlugin instance for testing.

    Returns:
        A ShfmtPlugin instance with mocked verify_tool_version.
    """
    with patch(
        "lintro.plugins.base.BaseToolPlugin._verify_tool_version",
        return_value=None,
    ):
        return ShfmtPlugin()


# Tests for default options


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", SHFMT_DEFAULT_TIMEOUT),
        ("indent", None),
        ("binary_next_line", False),
        ("switch_case_indent", False),
        ("space_redirects", False),
        ("language_dialect", None),
        ("simplify", False),
    ],
    ids=[
        "timeout_equals_default",
        "indent_is_none",
        "binary_next_line_is_false",
        "switch_case_indent_is_false",
        "space_redirects_is_false",
        "language_dialect_is_none",
        "simplify_is_false",
    ],
)
def test_default_options_values(
    shfmt_plugin: ShfmtPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        shfmt_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for ShfmtPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("indent", 0),
        ("indent", 2),
        ("indent", 4),
        ("binary_next_line", True),
        ("switch_case_indent", True),
        ("space_redirects", True),
        ("language_dialect", "bash"),
        ("language_dialect", "posix"),
        ("language_dialect", "mksh"),
        ("language_dialect", "bats"),
        ("simplify", True),
    ],
    ids=[
        "indent_0_tabs",
        "indent_2_spaces",
        "indent_4_spaces",
        "binary_next_line_true",
        "switch_case_indent_true",
        "space_redirects_true",
        "language_dialect_bash",
        "language_dialect_posix",
        "language_dialect_mksh",
        "language_dialect_bats",
        "simplify_true",
    ],
)
def test_set_options_valid(
    shfmt_plugin: ShfmtPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    shfmt_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(shfmt_plugin.options.get(option_name)).is_equal_to(option_value)


def test_set_options_language_dialect_case_insensitive(
    shfmt_plugin: ShfmtPlugin,
) -> None:
    """Set language_dialect with different case normalizes to lowercase.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(language_dialect="BASH")
    assert_that(shfmt_plugin.options.get("language_dialect")).is_equal_to("bash")


# Tests for ShfmtPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("indent", "four", "indent must be an integer"),
        ("indent", 4.5, "indent must be an integer"),
        ("binary_next_line", "yes", "binary_next_line must be a boolean"),
        ("binary_next_line", 1, "binary_next_line must be a boolean"),
        ("switch_case_indent", "true", "switch_case_indent must be a boolean"),
        ("space_redirects", "no", "space_redirects must be a boolean"),
        ("language_dialect", 123, "language_dialect must be a string"),
        ("language_dialect", "invalid", "Invalid language_dialect"),
        ("language_dialect", "sh", "Invalid language_dialect"),
        ("simplify", "yes", "simplify must be a boolean"),
    ],
    ids=[
        "invalid_indent_string",
        "invalid_indent_float",
        "invalid_binary_next_line_string",
        "invalid_binary_next_line_int",
        "invalid_switch_case_indent_string",
        "invalid_space_redirects_string",
        "invalid_language_dialect_int",
        "invalid_language_dialect_value",
        "invalid_language_dialect_sh",
        "invalid_simplify_string",
    ],
)
def test_set_options_invalid_type(
    shfmt_plugin: ShfmtPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        shfmt_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for ShfmtPlugin._build_common_args method


def test_build_common_args_no_options(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with no options set returns empty list.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    args = shfmt_plugin._build_common_args()
    assert_that(args).is_empty()


def test_build_common_args_with_indent(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with indent option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(indent=4)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-i")
    indent_idx = args.index("-i")
    assert_that(args[indent_idx + 1]).is_equal_to("4")


def test_build_common_args_with_indent_zero(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with indent=0 for tabs.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(indent=0)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-i")
    indent_idx = args.index("-i")
    assert_that(args[indent_idx + 1]).is_equal_to("0")


def test_build_common_args_with_binary_next_line(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with binary_next_line option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(binary_next_line=True)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-bn")


def test_build_common_args_with_switch_case_indent(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with switch_case_indent option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(switch_case_indent=True)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-ci")


def test_build_common_args_with_space_redirects(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with space_redirects option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(space_redirects=True)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-sr")


def test_build_common_args_with_language_dialect(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with language_dialect option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(language_dialect="bash")
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-ln")
    ln_idx = args.index("-ln")
    assert_that(args[ln_idx + 1]).is_equal_to("bash")


def test_build_common_args_with_simplify(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with simplify option.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(simplify=True)
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-s")


def test_build_common_args_with_all_options(shfmt_plugin: ShfmtPlugin) -> None:
    """Build common args with all options set.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
    """
    shfmt_plugin.set_options(
        indent=2,
        binary_next_line=True,
        switch_case_indent=True,
        space_redirects=True,
        language_dialect="posix",
        simplify=True,
    )
    args = shfmt_plugin._build_common_args()

    assert_that(args).contains("-i")
    assert_that(args).contains("-bn")
    assert_that(args).contains("-ci")
    assert_that(args).contains("-sr")
    assert_that(args).contains("-ln")
    assert_that(args).contains("-s")

    # Verify values
    indent_idx = args.index("-i")
    assert_that(args[indent_idx + 1]).is_equal_to("2")

    ln_idx = args.index("-ln")
    assert_that(args[ln_idx + 1]).is_equal_to("posix")


# Tests for ShfmtPlugin.check method


def test_check_with_mocked_subprocess_success(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no issues found.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\necho "hello"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = shfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_issues(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when shfmt finds formatting problems.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\nif [  "$foo" = "bar" ]; then\necho "match"\nfi\n')

    shfmt_diff_output = f"""--- {test_file}
+++ {test_file}
@@ -1,4 +1,4 @@
 #!/bin/bash
-if [  "$foo" = "bar" ]; then
+if [ "$foo" = "bar" ]; then
 echo "match"
 fi"""

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            return_value=(False, shfmt_diff_output),
        ):
            result = shfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


def test_check_with_timeout(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\necho "hello"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["shfmt"], timeout=30),
        ):
            result = shfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()


def test_check_with_no_shell_files(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no shell files found.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_sh_file = tmp_path / "test.txt"
    non_sh_file.write_text("Not a shell file")

    with patch.object(shfmt_plugin, "_verify_tool_version", return_value=None):
        result = shfmt_plugin.check([str(non_sh_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No")


# Tests for ShfmtPlugin.fix method


def test_fix_with_mocked_subprocess_success(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when fixes are applied.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\nif [  "$foo" = "bar" ]; then\necho "match"\nfi\n')

    shfmt_diff_output = f"""--- {test_file}
+++ {test_file}
@@ -1,4 +1,4 @@
 #!/bin/bash
-if [  "$foo" = "bar" ]; then
+if [ "$foo" = "bar" ]; then
 echo "match"
 fi"""

    call_count = 0

    def mock_run_subprocess(
        cmd: list[str],
        timeout: int,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        """Mock subprocess that returns diff on check, success on fix.

        Args:
            cmd: Command list.
            timeout: Timeout in seconds.
            cwd: Working directory.

        Returns:
            Tuple of (success, output).
        """
        nonlocal call_count
        call_count += 1
        # First call is check with -d flag
        if "-d" in cmd:
            return (False, shfmt_diff_output)
        # Second call is fix with -w flag
        return (True, "")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            side_effect=mock_run_subprocess,
        ):
            result = shfmt_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.fixed_issues_count).is_greater_than(0)


def test_fix_with_nothing_to_fix(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when no fixes needed.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\necho "hello"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = shfmt_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No fixes needed")


def test_fix_with_timeout(
    shfmt_plugin: ShfmtPlugin,
    tmp_path: Path,
) -> None:
    """Fix handles timeout correctly.

    Args:
        shfmt_plugin: The ShfmtPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_script.sh"
    test_file.write_text('#!/bin/bash\necho "hello"\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            shfmt_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["shfmt"], timeout=30),
        ):
            result = shfmt_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_false()


# Tests for output parsing


def test_parse_shfmt_output_single_file() -> None:
    """Parse single file diff from shfmt output."""
    output = """--- script.sh
+++ script.sh
@@ -1,3 +1,3 @@
-if [  "$foo" = "bar" ]; then
+if [ "$foo" = "bar" ]; then
   echo "match"
 fi"""
    issues = parse_shfmt_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("script.sh")
    assert_that(issues[0].line).is_equal_to(1)
    assert_that(issues[0].message).contains("Needs formatting")
    assert_that(issues[0].fixable).is_true()


def test_parse_shfmt_output_multiple_files() -> None:
    """Parse multiple files diff from shfmt output."""
    output = """--- script1.sh
+++ script1.sh
@@ -1,2 +1,2 @@
-echo  "hello"
+echo "hello"
--- script2.sh
+++ script2.sh
@@ -1,2 +1,2 @@
-if [  1 ]; then
+if [ 1 ]; then"""
    issues = parse_shfmt_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("script1.sh")
    assert_that(issues[1].file).is_equal_to("script2.sh")


def test_parse_shfmt_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_shfmt_output("")

    assert_that(issues).is_empty()


def test_parse_shfmt_output_none() -> None:
    """Parse None output returns empty list."""
    issues = parse_shfmt_output(None)

    assert_that(issues).is_empty()


def test_parse_shfmt_output_with_orig_suffix() -> None:
    """Parse diff with .orig suffix in header."""
    output = """--- script.sh.orig
+++ script.sh
@@ -1,2 +1,2 @@
-echo  "hello"
+echo "hello" """
    issues = parse_shfmt_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("script.sh")
