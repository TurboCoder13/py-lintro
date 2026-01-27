"""Integration tests for TypeScript Compiler (tsc) tool definition.

These tests require tsc (typescript) to be installed and available in PATH.
They verify the TscPlugin definition, check command, and set_options method.
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

# Skip all tests if tsc is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("tsc") is None,
    reason="tsc not installed",
)


# --- Tests for TscPlugin definition ---


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("name", "tsc"),
        ("can_fix", False),
    ],
    ids=["name", "can_fix"],
)
def test_definition_attributes(
    get_plugin: Callable[[str], BaseToolPlugin],
    attr: str,
    expected: object,
) -> None:
    """Verify TscPlugin definition has correct attribute values.

    Tests that the plugin definition exposes the expected values for
    name and can_fix attributes.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        attr: The attribute name to check on the definition.
        expected: The expected value of the attribute.
    """
    tsc_plugin = get_plugin("tsc")
    assert_that(getattr(tsc_plugin.definition, attr)).is_equal_to(expected)


def test_definition_file_patterns(get_plugin: Callable[[str], BaseToolPlugin]) -> None:
    """Verify TscPlugin definition includes TypeScript file patterns.

    Tests that the plugin is configured to handle TypeScript files (*.ts, *.tsx).

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    tsc_plugin = get_plugin("tsc")
    assert_that(tsc_plugin.definition.file_patterns).contains("*.ts")
    assert_that(tsc_plugin.definition.file_patterns).contains("*.tsx")


# --- Integration tests for tsc check command ---


def test_check_file_with_type_errors(
    get_plugin: Callable[[str], BaseToolPlugin],
    tsc_violation_file: str,
) -> None:
    """Verify tsc check detects type errors in problematic files.

    Runs tsc on a file containing deliberate type violations and verifies
    that issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tsc_violation_file: Path to file with type errors from test_samples.
    """
    tsc_plugin = get_plugin("tsc")
    result = tsc_plugin.check([tsc_violation_file], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("tsc")
    assert_that(result.issues_count).is_greater_than(0)


def test_check_type_correct_file(
    get_plugin: Callable[[str], BaseToolPlugin],
    tsc_clean_file: str,
) -> None:
    """Verify tsc check passes on type-correct files.

    Runs tsc on a properly typed file and verifies no issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tsc_clean_file: Path to file with correct types from test_samples.
    """
    tsc_plugin = get_plugin("tsc")
    result = tsc_plugin.check([tsc_clean_file], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("tsc")
    assert_that(result.issues_count).is_equal_to(0)


def test_check_empty_directory(
    get_plugin: Callable[[str], BaseToolPlugin],
    tmp_path: Path,
) -> None:
    """Verify tsc check handles empty directories gracefully.

    Runs tsc on an empty directory and verifies a result is returned
    without errors.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tmp_path: Pytest fixture providing a temporary directory.
    """
    tsc_plugin = get_plugin("tsc")
    result = tsc_plugin.check([str(tmp_path)], {})

    assert_that(result).is_not_none()


# --- Tests for TscPlugin.set_options method ---


@pytest.mark.parametrize(
    ("option_name", "option_value", "expected"),
    [
        ("project", "tsconfig.json", "tsconfig.json"),
        ("strict", True, True),
        ("skip_lib_check", True, True),
    ],
    ids=["project", "strict", "skip_lib_check"],
)
def test_set_options(
    get_plugin: Callable[[str], BaseToolPlugin],
    option_name: str,
    option_value: object,
    expected: object,
) -> None:
    """Verify TscPlugin.set_options correctly sets various options.

    Tests that plugin options can be set and retrieved correctly.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
        expected: Expected value when retrieving the option.
    """
    tsc_plugin = get_plugin("tsc")
    tsc_plugin.set_options(**{option_name: option_value})
    assert_that(tsc_plugin.options.get(option_name)).is_equal_to(expected)
