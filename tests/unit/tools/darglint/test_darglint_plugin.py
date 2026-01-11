"""Unit tests for darglint plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.enums.darglint_strictness import DarglintStrictness
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.tools.definitions.darglint import (
    DARGLINT_DEFAULT_STRICTNESS,
    DARGLINT_DEFAULT_TIMEOUT,
    DARGLINT_DEFAULT_VERBOSITY,
    DARGLINT_MAX_VERBOSITY,
    DARGLINT_MIN_VERBOSITY,
    DarglintPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def darglint_plugin() -> DarglintPlugin:
    """Provide a DarglintPlugin instance for testing.

    Returns:
        A DarglintPlugin instance.
    """
    with patch(
        "lintro.tools.definitions.darglint.load_darglint_config",
        return_value={},
    ):
        return DarglintPlugin()


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", DARGLINT_DEFAULT_TIMEOUT),
        ("verbosity", DARGLINT_DEFAULT_VERBOSITY),
        ("strictness", DARGLINT_DEFAULT_STRICTNESS),
        ("ignore", None),
        ("ignore_regex", None),
        ("ignore_syntax", False),
    ],
    ids=[
        "timeout_equals_default",
        "verbosity_equals_default",
        "strictness_equals_default",
        "ignore_is_none",
        "ignore_regex_is_none",
        "ignore_syntax_is_false",
    ],
)
def test_default_options_values(
    darglint_plugin: DarglintPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        darglint_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for DarglintPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("ignore", ["DAR101", "DAR102"]),
        ("ignore_regex", "DAR1.*"),
        ("ignore_syntax", True),
        ("message_template", "{path}:{line}:{msg}"),
        ("verbosity", 1),
        ("verbosity", 2),
        ("verbosity", 3),
        ("strictness", "short"),
        ("strictness", "long"),
        ("strictness", "full"),
    ],
    ids=[
        "ignore_list",
        "ignore_regex",
        "ignore_syntax",
        "message_template",
        "verbosity_1",
        "verbosity_2",
        "verbosity_3",
        "strictness_short",
        "strictness_long",
        "strictness_full",
    ],
)
def test_set_options_valid(
    darglint_plugin: DarglintPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    darglint_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(darglint_plugin.options.get(option_name)).is_equal_to(option_value)


def test_set_options_strictness_enum(darglint_plugin: DarglintPlugin) -> None:
    """Set strictness option with enum value.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(strictness=DarglintStrictness.SHORT)
    assert_that(darglint_plugin.options.get("strictness")).is_equal_to("short")


# Tests for DarglintPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("ignore", "DAR101", "ignore must be a list"),
        ("ignore_regex", 123, "ignore_regex must be a string"),
        ("ignore_syntax", "yes", "ignore_syntax must be a boolean"),
        ("message_template", 123, "message_template must be a string"),
        ("verbosity", "high", "verbosity must be an integer"),
        ("verbosity", 0, f"verbosity must be at least {DARGLINT_MIN_VERBOSITY}"),
        ("verbosity", 4, f"verbosity must be at most {DARGLINT_MAX_VERBOSITY}"),
    ],
    ids=[
        "invalid_ignore_type",
        "invalid_ignore_regex_type",
        "invalid_ignore_syntax_type",
        "invalid_message_template_type",
        "invalid_verbosity_type",
        "invalid_verbosity_too_low",
        "invalid_verbosity_too_high",
    ],
)
def test_set_options_invalid_type(
    darglint_plugin: DarglintPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        darglint_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for DarglintPlugin._build_command method


def test_build_command_basic(darglint_plugin: DarglintPlugin) -> None:
    """Build basic command without extra options.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    cmd = darglint_plugin._build_command()
    assert_that(cmd).contains("darglint")
    # Default verbosity and strictness should be included
    assert_that(
        "--verbosity" in cmd or any("verbosity" in str(c) for c in cmd),
    ).is_true()


def test_build_command_with_ignore(darglint_plugin: DarglintPlugin) -> None:
    """Build command with ignore option.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(ignore=["DAR101", "DAR102"])
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--ignore")
    # Find the index of --ignore and check the next element
    ignore_idx = cmd.index("--ignore")
    assert_that(cmd[ignore_idx + 1]).is_equal_to("DAR101,DAR102")


def test_build_command_with_ignore_regex(darglint_plugin: DarglintPlugin) -> None:
    """Build command with ignore_regex option.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(ignore_regex="DAR1.*")
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--ignore-regex")
    ignore_regex_idx = cmd.index("--ignore-regex")
    assert_that(cmd[ignore_regex_idx + 1]).is_equal_to("DAR1.*")


def test_build_command_with_ignore_syntax(darglint_plugin: DarglintPlugin) -> None:
    """Build command with ignore_syntax option.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(ignore_syntax=True)
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--ignore-syntax")


def test_build_command_with_verbosity(darglint_plugin: DarglintPlugin) -> None:
    """Build command with verbosity option.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(verbosity=3)
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--verbosity")
    verbosity_idx = cmd.index("--verbosity")
    assert_that(cmd[verbosity_idx + 1]).is_equal_to("3")


def test_build_command_with_strictness(darglint_plugin: DarglintPlugin) -> None:
    """Build command with strictness option.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(strictness="short")
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--strictness")
    strictness_idx = cmd.index("--strictness")
    assert_that(cmd[strictness_idx + 1]).is_equal_to("short")


def test_build_command_with_all_options(darglint_plugin: DarglintPlugin) -> None:
    """Build command with all options set.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
    """
    darglint_plugin.set_options(
        ignore=["DAR101"],
        ignore_regex="DAR2.*",
        ignore_syntax=True,
        verbosity=1,
        strictness="long",
    )
    cmd = darglint_plugin._build_command()

    assert_that(cmd).contains("--ignore")
    assert_that(cmd).contains("--ignore-regex")
    assert_that(cmd).contains("--ignore-syntax")
    assert_that(cmd).contains("--verbosity")
    assert_that(cmd).contains("--strictness")


# Tests for DarglintPlugin.check method


def test_check_with_mocked_subprocess_success(
    darglint_plugin: DarglintPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no issues found.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    # Create a test file
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            darglint_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = darglint_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_issues(
    darglint_plugin: DarglintPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when darglint finds problems.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('def foo():\n    """Missing return."""\n    return 1\n')

    darglint_output = f"{test_file}:foo:1: DAR201 Missing return in docstring"

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            darglint_plugin,
            "_run_subprocess",
            return_value=(False, darglint_output),
        ):
            result = darglint_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


def test_check_with_timeout(
    darglint_plugin: DarglintPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            darglint_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["darglint"], timeout=15),
        ):
            result = darglint_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    # The timeout should be recorded as an issue
    assert_that(result.issues_count).is_greater_than(0)


def test_check_with_no_python_files(
    darglint_plugin: DarglintPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no Python files found.

    Args:
        darglint_plugin: The DarglintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_py_file = tmp_path / "test.txt"
    non_py_file.write_text("Not a python file")

    with patch.object(darglint_plugin, "_verify_tool_version", return_value=None):
        result = darglint_plugin.check([str(non_py_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No")


# Tests for output parsing


def test_parse_darglint_output_single_issue() -> None:
    """Parse single issue from darglint output."""
    output = "test.py:func:10: DAR101 Missing parameter in docstring"
    issues = parse_darglint_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].code).is_equal_to("DAR101")
    assert_that(issues[0].message).contains("Missing parameter")


def test_parse_darglint_output_multiple_issues() -> None:
    """Parse multiple issues from darglint output."""
    output = """test.py:func1:10: DAR101 Missing parameter in docstring
test.py:func2:20: DAR201 Missing return in docstring"""
    issues = parse_darglint_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].code).is_equal_to("DAR101")
    assert_that(issues[1].code).is_equal_to("DAR201")


def test_parse_darglint_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_darglint_output("")

    assert_that(issues).is_empty()


def test_parse_darglint_output_module_level() -> None:
    """Parse module-level issue without function name."""
    output = "test.py:5: DAR003 Module docstring missing"
    issues = parse_darglint_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.py")
    assert_that(issues[0].line).is_equal_to(5)
    assert_that(issues[0].code).is_equal_to("DAR003")


def test_parse_darglint_output_with_colon_in_message() -> None:
    """Parse output with colons in the message."""
    output = "test.py:func:10: DAR101: Missing parameter in docstring: x"
    issues = parse_darglint_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].message).contains("Missing parameter")


def test_parse_darglint_output_multiline_message() -> None:
    """Parse output with multiline messages."""
    output = """test.py:func:10: DAR101 Missing parameter
    : x
    : y"""
    issues = parse_darglint_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].message).contains("Missing parameter")
    assert_that(issues[0].message).contains("x")
    assert_that(issues[0].message).contains("y")


# Tests for plugin initialization with config


def test_plugin_init_with_exclude_dirs() -> None:
    """Plugin initialization applies exclude_dirs from config."""
    config = {"exclude_dirs": ["tests", "docs"]}
    with patch(
        "lintro.tools.definitions.darglint.load_darglint_config",
        return_value=config,
    ):
        plugin = DarglintPlugin()

    assert_that(plugin.exclude_patterns).contains("tests/*")
    assert_that(plugin.exclude_patterns).contains("docs/*")


def test_plugin_init_with_timeout_config() -> None:
    """Plugin initialization applies timeout from config."""
    config = {"timeout": 30}
    with patch(
        "lintro.tools.definitions.darglint.load_darglint_config",
        return_value=config,
    ):
        plugin = DarglintPlugin()

    assert_that(plugin.options.get("timeout")).is_equal_to(30)


def test_plugin_init_with_exclude_files() -> None:
    """Plugin initialization applies exclude_files from config."""
    config = {"exclude_files": ["conftest.py", "setup.py"]}
    with patch(
        "lintro.tools.definitions.darglint.load_darglint_config",
        return_value=config,
    ):
        plugin = DarglintPlugin()

    assert_that(plugin.exclude_patterns).contains("conftest.py")
    assert_that(plugin.exclude_patterns).contains("setup.py")
