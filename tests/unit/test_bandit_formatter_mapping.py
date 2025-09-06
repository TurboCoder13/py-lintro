"""Unit tests for Bandit formatter integration and mapping.

These tests verify that Bandit is registered in the centralized formatter
mapping and that formatted output is produced via the shared helper.
"""

from assertpy import assert_that

from lintro.parsers.bandit.bandit_issue import BanditIssue
from lintro.utils.tool_utils import TOOL_TABLE_FORMATTERS, format_tool_output


def test_bandit_present_in_tool_table_formatters() -> None:
    """Assert Bandit is registered in the centralized formatter mapping."""
    assert_that(TOOL_TABLE_FORMATTERS).contains("bandit")


def test_format_tool_output_bandit_across_styles() -> None:
    """Verify Bandit issues render across supported output styles."""
    sample_issue = BanditIssue(
        file="src/app.py",
        line=10,
        col_offset=4,
        issue_severity="HIGH",
        issue_confidence="HIGH",
        test_id="B602",
        test_name="subprocess_popen_with_shell_equals_true",
        issue_text="subprocess call with shell=True identified, security issue.",
        more_info="https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html",
    )
    issues = [sample_issue]
    styles: list[str] = ["grid", "plain", "markdown", "html", "json", "csv"]
    for style in styles:
        rendered = format_tool_output(
            tool_name="bandit",
            output="",
            output_format=style,
            issues=issues,
        )
        assert_that(isinstance(rendered, str)).is_true()
        assert_that(rendered.strip()).is_not_equal_to("")
