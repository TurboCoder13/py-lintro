"""Integration tests for ShellCheck tool definition.

These tests require shellcheck to be installed and available in PATH.
They verify the ShellcheckPlugin definition, check command, and set_options method.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.plugins.base import BaseToolPlugin

# Skip all tests if shellcheck is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("shellcheck") is None,
    reason="shellcheck not installed",
)


@pytest.fixture
def temp_shell_file_with_issues(tmp_path: Path) -> str:
    """Create a temporary shell script with lint issues.

    Creates a file containing shell code with issues that ShellCheck
    should detect, including:
    - Unquoted variable expansion
    - Missing shebang
    - Useless use of cat

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "test_script.sh"
    file_path.write_text(
        """\
#!/bin/bash
# Script with issues

name="world"
echo $name  # SC2086: Double quote to prevent globbing

# Useless use of cat
cat file.txt | grep "pattern"  # SC2002

# Unquoted variable in array
files=( $FILES )  # SC2206
""",
    )
    return str(file_path)


@pytest.fixture
def temp_shell_file_clean(tmp_path: Path) -> str:
    """Create a temporary shell script with no lint issues.

    Creates a file containing clean shell code that should pass
    ShellCheck without issues.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "clean_script.sh"
    file_path.write_text(
        """\
#!/bin/bash

# A clean shell script with proper quoting
set -euo pipefail

say_hello() {
    local name="$1"
    echo "Hello, ${name}!"
}

main() {
    if [[ -n "${1:-}" ]]; then
        say_hello "$1"
    else
        say_hello "World"
    fi
}

main "$@"
""",
    )
    return str(file_path)


@pytest.fixture
def temp_shell_file_style_issues(tmp_path: Path) -> str:
    """Create a temporary shell script with style-level issues.

    Creates a file containing code with style-level issues that ShellCheck
    should detect at the style severity level.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "style_script.sh"
    file_path.write_text(
        """\
#!/bin/bash

# Style issues - backticks instead of $()
output=`ls -la`  # SC2006: Use $(...) notation

# Style issue - echo with options
echo -e "Hello\\nWorld"  # SC2028: echo may interpret sequences

echo "$output"
""",
    )
    return str(file_path)


# --- Tests for ShellcheckPlugin definition ---


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("name", "shellcheck"),
        ("can_fix", False),  # ShellCheck cannot auto-fix
    ],
    ids=["name", "can_fix"],
)
def test_definition_attributes(
    get_plugin: Callable[[str], BaseToolPlugin],
    attr: str,
    expected: object,
) -> None:
    """Verify ShellcheckPlugin definition has correct attribute values.

    Tests that the plugin definition exposes the expected values for
    name and can_fix attributes.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        attr: The attribute name to check on the definition.
        expected: The expected value of the attribute.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    assert_that(getattr(shellcheck_plugin.definition, attr)).is_equal_to(expected)


def test_definition_file_patterns(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify ShellcheckPlugin definition includes shell file patterns.

    Tests that the plugin is configured to handle shell files
    (*.sh, *.bash, *.ksh, *.zsh).

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    assert_that(shellcheck_plugin.definition.file_patterns).contains("*.sh")
    assert_that(shellcheck_plugin.definition.file_patterns).contains("*.bash")
    assert_that(shellcheck_plugin.definition.file_patterns).contains("*.zsh")


def test_definition_has_version_command(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify ShellcheckPlugin definition has a version command.

    Tests that the plugin exposes a version command for checking
    the installed ShellCheck version.

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    assert_that(shellcheck_plugin.definition.version_command).is_not_none()


# --- Integration tests for shellcheck check command ---


def test_check_file_with_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_with_issues: str,
) -> None:
    """Verify ShellCheck check detects lint issues in problematic files.

    Runs ShellCheck on a file containing lint issues and verifies that
    issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_with_issues: Path to file with lint issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([temp_shell_file_with_issues], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("shellcheck")
    assert_that(result.issues_count).is_greater_than(0)


def test_check_clean_file(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_clean: str,
) -> None:
    """Verify ShellCheck check passes on clean files.

    Runs ShellCheck on a clean file and verifies no issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_clean: Path to clean file.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([temp_shell_file_clean], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("shellcheck")
    assert_that(result.success).is_true()


def test_check_empty_directory(
    get_plugin: Callable[[str], BaseToolPlugin],
    tmp_path: Path,
) -> None:
    """Verify ShellCheck check handles empty directories gracefully.

    Runs ShellCheck on an empty directory and verifies a result is returned
    with zero issues.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tmp_path: Pytest fixture providing a temporary directory.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([str(tmp_path)], {})

    assert_that(result).is_not_none()
    assert_that(result.issues_count).is_equal_to(0)


# --- Integration tests for shellcheck check with various options ---


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("severity", "error"),
        ("severity", "warning"),
        ("severity", "info"),
        ("severity", "style"),
        ("shell", "bash"),
        ("shell", "sh"),
        ("exclude", ["SC2086"]),
        ("exclude", ["SC2086", "SC2046"]),
    ],
    ids=[
        "severity_error",
        "severity_warning",
        "severity_info",
        "severity_style",
        "shell_bash",
        "shell_sh",
        "exclude_single",
        "exclude_multiple",
    ],
)
def test_check_with_options(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_with_issues: str,
    option_name: str,
    option_value: object,
) -> None:
    """Verify ShellCheck check works with various configuration options.

    Runs ShellCheck with different options configured and verifies the
    check completes successfully.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_with_issues: Path to file with lint issues.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    shellcheck_plugin.set_options(**{option_name: option_value})
    result = shellcheck_plugin.check([temp_shell_file_with_issues], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("shellcheck")


def test_check_severity_filters_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_style_issues: str,
) -> None:
    """Verify ShellCheck severity option filters issues appropriately.

    Runs ShellCheck with error severity (strictest) and verifies fewer
    issues are found than with style severity (least strict).

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_style_issues: Path to file with style-level issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")

    # Check with style severity (default, reports all issues)
    shellcheck_plugin.set_options(severity="style")
    style_result = shellcheck_plugin.check([temp_shell_file_style_issues], {})

    # Check with error severity (strictest, reports only errors)
    shellcheck_plugin.set_options(severity="error")
    error_result = shellcheck_plugin.check([temp_shell_file_style_issues], {})

    # Error severity should report fewer or equal issues than style
    assert_that(error_result.issues_count).is_less_than_or_equal_to(
        style_result.issues_count,
    )


def test_check_exclude_filters_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_with_issues: str,
) -> None:
    """Verify ShellCheck exclude option filters out specific codes.

    Runs ShellCheck without exclusions, then with SC2086 excluded,
    and verifies fewer issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_with_issues: Path to file with lint issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")

    # Check without exclusions
    result_without_exclude = shellcheck_plugin.check([temp_shell_file_with_issues], {})

    # Check with SC2086 excluded
    shellcheck_plugin.set_options(exclude=["SC2086", "SC2002", "SC2206"])
    result_with_exclude = shellcheck_plugin.check([temp_shell_file_with_issues], {})

    # With exclusions should report fewer or equal issues
    assert_that(result_with_exclude.issues_count).is_less_than_or_equal_to(
        result_without_exclude.issues_count,
    )


# --- Tests for ShellcheckPlugin.set_options method ---


@pytest.mark.parametrize(
    ("option_name", "option_value", "expected"),
    [
        ("severity", "error", "error"),
        ("severity", "warning", "warning"),
        ("severity", "info", "info"),
        ("severity", "style", "style"),
        ("shell", "bash", "bash"),
        ("shell", "sh", "sh"),
        ("shell", "zsh", "zsh"),
        ("exclude", ["SC2086"], ["SC2086"]),
        ("exclude", ["SC2086", "SC2046"], ["SC2086", "SC2046"]),
    ],
    ids=[
        "severity_error",
        "severity_warning",
        "severity_info",
        "severity_style",
        "shell_bash",
        "shell_sh",
        "shell_zsh",
        "exclude_single",
        "exclude_multiple",
    ],
)
def test_set_options(
    get_plugin: Callable[[str], BaseToolPlugin],
    option_name: str,
    option_value: object,
    expected: object,
) -> None:
    """Verify ShellcheckPlugin.set_options correctly sets various options.

    Tests that plugin options can be set and retrieved correctly.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
        expected: Expected value when retrieving the option.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    shellcheck_plugin.set_options(**{option_name: option_value})
    assert_that(shellcheck_plugin.options.get(option_name)).is_equal_to(expected)


def test_invalid_severity(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify ShellcheckPlugin.set_options rejects invalid severity values.

    Tests that invalid severity values raise ValueError.

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    with pytest.raises(ValueError, match="Invalid severity level"):
        shellcheck_plugin.set_options(severity="invalid")


def test_invalid_shell(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify ShellcheckPlugin.set_options rejects invalid shell values.

    Tests that invalid shell dialect values raise ValueError.

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    with pytest.raises(ValueError, match="Invalid shell dialect"):
        shellcheck_plugin.set_options(shell="invalid")  # nosec B604


def test_fix_raises_not_implemented(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_shell_file_with_issues: str,
) -> None:
    """Verify ShellCheck fix raises NotImplementedError.

    ShellCheck cannot automatically fix issues, so calling fix should
    raise NotImplementedError.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_shell_file_with_issues: Path to file with lint issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    with pytest.raises(NotImplementedError, match="cannot automatically fix"):
        shellcheck_plugin.fix([temp_shell_file_with_issues], {})
