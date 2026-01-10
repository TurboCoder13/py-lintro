"""Tests for YamllintPlugin.check method."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.yamllint.yamllint_issue import YamllintIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


def test_check_success_no_issues(yamllint_plugin: YamllintPlugin) -> None:
    """Check returns success when no issues found.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(yamllint_plugin, "_process_single_file") as mock_process,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch.object(yamllint_plugin, "_load_yamllint_ignore_patterns") as mock_ignore,
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.files = ["test.yml"]
        mock_ctx.timeout = 15
        mock_prepare.return_value = mock_ctx

        mock_config.return_value = None
        mock_ignore.return_value = []

        # Mock the results dict modification
        def process_side_effect(
            file_path: str,
            timeout: int,
            results: dict[str, Any],
        ) -> None:
            pass  # No issues added

        mock_process.side_effect = process_side_effect

        result = yamllint_plugin.check(["/tmp/test.yml"], {})

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.name).is_equal_to("yamllint")


def test_check_failure_with_issues(yamllint_plugin: YamllintPlugin) -> None:
    """Check returns failure when issues found.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(yamllint_plugin, "_process_single_file") as mock_process,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch.object(yamllint_plugin, "_load_yamllint_ignore_patterns") as mock_ignore,
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.files = ["test.yml"]
        mock_ctx.timeout = 15
        mock_prepare.return_value = mock_ctx

        mock_config.return_value = None
        mock_ignore.return_value = []

        # Mock the results dict modification to add issues
        def process_side_effect(
            file_path: str,
            timeout: int,
            results: dict[str, Any],
        ) -> None:
            results["all_success"] = False
            results["total_issues"] = 1
            results["all_issues"].append(
                YamllintIssue(
                    file="test.yml",
                    line=5,
                    column=1,
                    level=SeverityLevel.ERROR,
                    rule="trailing-spaces",
                    message="trailing spaces",
                ),
            )

        mock_process.side_effect = process_side_effect

        result = yamllint_plugin.check(["/tmp/test.yml"], {})

        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(1)


def test_check_early_return_when_should_skip(yamllint_plugin: YamllintPlugin) -> None:
    """Check returns early result when should_skip is True.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with patch.object(yamllint_plugin, "_prepare_execution") as mock_prepare:
        mock_ctx = MagicMock()
        mock_ctx.should_skip = True
        mock_ctx.early_result = MagicMock(success=True, issues_count=0)
        mock_prepare.return_value = mock_ctx

        result = yamllint_plugin.check(["/tmp"], {})

        assert_that(result.success).is_true()


def test_check_no_files_after_filtering(yamllint_plugin: YamllintPlugin) -> None:
    """Check returns success message when no files after filtering.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch.object(yamllint_plugin, "_load_yamllint_ignore_patterns") as mock_ignore,
        patch.object(yamllint_plugin, "_should_ignore_file") as mock_should_ignore,
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.files = ["test.yml"]
        mock_ctx.timeout = 15
        mock_prepare.return_value = mock_ctx

        mock_config.return_value = ".yamllint"
        mock_ignore.return_value = ["test.yml"]
        mock_should_ignore.return_value = True

        result = yamllint_plugin.check(["/tmp/test.yml"], {})

        assert_that(result.success).is_true()
        assert_that(result.output).contains("No YAML files found to check")


def test_check_with_strict_option(yamllint_plugin: YamllintPlugin) -> None:
    """Check includes strict flag when option is set.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yamllint_plugin.set_options(strict=True)
    assert_that(yamllint_plugin.options.get("strict")).is_true()


def test_check_with_relaxed_option(yamllint_plugin: YamllintPlugin) -> None:
    """Check includes relaxed flag when option is set.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yamllint_plugin.set_options(relaxed=True)
    assert_that(yamllint_plugin.options.get("relaxed")).is_true()


def test_check_with_no_warnings_option(yamllint_plugin: YamllintPlugin) -> None:
    """Check includes no_warnings flag when option is set.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yamllint_plugin.set_options(no_warnings=True)
    assert_that(yamllint_plugin.options.get("no_warnings")).is_true()
