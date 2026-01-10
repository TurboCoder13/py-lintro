"""Tests for YamllintPlugin output parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.yamllint.yamllint_issue import YamllintIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


def test_check_parses_yamllint_output_correctly(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Check correctly parses yamllint output with issues.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(yamllint_plugin, "_process_single_file") as mock_process,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch.object(yamllint_plugin, "_load_yamllint_ignore_patterns") as mock_ignore,
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.files = ["file1.yml", "file2.yml"]
        mock_ctx.timeout = 15
        mock_prepare.return_value = mock_ctx

        mock_config.return_value = None
        mock_ignore.return_value = []

        # Mock the results dict modification
        call_count = [0]

        def process_side_effect(
            file_path: str,
            timeout: int,
            results: dict[str, Any],
        ) -> None:
            call_count[0] += 1
            if call_count[0] == 1:
                results["all_success"] = False
                results["total_issues"] += 1
                results["all_issues"].append(
                    YamllintIssue(
                        file="file1.yml",
                        line=3,
                        column=1,
                        level=SeverityLevel.WARNING,
                        rule="document-start",
                        message='missing document start "---"',
                    ),
                )
            elif call_count[0] == 2:
                results["total_issues"] += 1
                results["all_issues"].append(
                    YamllintIssue(
                        file="file2.yml",
                        line=10,
                        column=81,
                        level=SeverityLevel.ERROR,
                        rule="line-length",
                        message="line too long (120 > 80 characters)",
                    ),
                )

        mock_process.side_effect = process_side_effect

        result = yamllint_plugin.check(["/tmp"], {})

        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(2)
        assert_that(result.issues).is_not_none()
        first_issue = cast(YamllintIssue, result.issues[0])  # type: ignore[index]  # validated via is_not_none
        second_issue = cast(YamllintIssue, result.issues[1])  # type: ignore[index]  # validated via is_not_none
        assert_that(first_issue.file).is_equal_to("file1.yml")
        assert_that(first_issue.rule).is_equal_to("document-start")
        assert_that(second_issue.file).is_equal_to("file2.yml")
        assert_that(second_issue.rule).is_equal_to("line-length")
