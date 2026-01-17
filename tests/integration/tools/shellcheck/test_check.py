"""Tests for ShellcheckPlugin check command.

These tests verify the check command works correctly on various inputs.
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

pytestmark = pytest.mark.skipif(
    shutil.which("shellcheck") is None,
    reason="shellcheck not installed",
)


def test_check_file_with_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    shellcheck_violation_file: str,
) -> None:
    """Verify ShellCheck check detects lint issues in problematic files.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        shellcheck_violation_file: Path to file with lint issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([shellcheck_violation_file], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("shellcheck")
    assert_that(result.issues_count).is_greater_than(0)


def test_check_clean_file(
    get_plugin: Callable[[str], BaseToolPlugin],
    shellcheck_clean_file: str,
) -> None:
    """Verify ShellCheck check passes on clean files.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        shellcheck_clean_file: Path to clean file.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([shellcheck_clean_file], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("shellcheck")
    assert_that(result.success).is_true()


def test_check_empty_directory(
    get_plugin: Callable[[str], BaseToolPlugin],
    tmp_path: Path,
) -> None:
    """Verify ShellCheck check handles empty directories gracefully.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tmp_path: Pytest fixture providing a temporary directory.
    """
    shellcheck_plugin = get_plugin("shellcheck")
    result = shellcheck_plugin.check([str(tmp_path)], {})

    assert_that(result).is_not_none()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_severity_filters_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    shellcheck_style_issues_file: str,
) -> None:
    """Verify ShellCheck severity option filters issues appropriately.

    Runs ShellCheck with error severity (strictest) and verifies fewer
    issues are found than with style severity (least strict).

    Args:
        get_plugin: Fixture factory to get plugin instances.
        shellcheck_style_issues_file: Path to file with style-level issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")

    # Check with style severity (default, reports all issues)
    shellcheck_plugin.set_options(severity="style")
    style_result = shellcheck_plugin.check([shellcheck_style_issues_file], {})

    # Check with error severity (strictest, reports only errors)
    shellcheck_plugin.set_options(severity="error")
    error_result = shellcheck_plugin.check([shellcheck_style_issues_file], {})

    # Error severity should report fewer or equal issues than style
    assert_that(error_result.issues_count).is_less_than_or_equal_to(
        style_result.issues_count,
    )


def test_check_exclude_filters_issues(
    get_plugin: Callable[[str], BaseToolPlugin],
    shellcheck_violation_file: str,
) -> None:
    """Verify ShellCheck exclude option filters out specific codes.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        shellcheck_violation_file: Path to file with lint issues.
    """
    shellcheck_plugin = get_plugin("shellcheck")

    # Check without exclusions
    result_without_exclude = shellcheck_plugin.check([shellcheck_violation_file], {})

    # Check with common codes excluded
    shellcheck_plugin.set_options(exclude=["SC2086", "SC2002", "SC2206"])
    result_with_exclude = shellcheck_plugin.check([shellcheck_violation_file], {})

    # With exclusions should report fewer or equal issues
    assert_that(result_with_exclude.issues_count).is_less_than_or_equal_to(
        result_without_exclude.issues_count,
    )
