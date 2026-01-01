"""Unit tests for Biome formatter functionality."""

from assertpy import assert_that

from lintro.formatters.tools.biome_formatter import (
    BiomeTableDescriptor,
    format_biome_issues,
)
from lintro.parsers.biome.biome_issue import BiomeIssue


def test_biome_table_descriptor_columns() -> None:
    """Test BiomeTableDescriptor returns correct columns."""
    descriptor = BiomeTableDescriptor()
    columns = descriptor.get_columns()
    expected = ["File", "Line", "Column", "Code", "Severity", "Message"]
    assert_that(columns).is_equal_to(expected)


def test_biome_table_descriptor_rows() -> None:
    """Test BiomeTableDescriptor generates correct rows."""
    descriptor = BiomeTableDescriptor()

    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/test",
            severity="error",
            message="Test error",
        ),
        BiomeIssue(
            file="src/utils.js",
            line=10,
            column=15,
            code="lint/warning",
            severity="warning",
            message="Test warning",
        ),
    ]

    rows = descriptor.get_rows(issues)
    expected = [
        ["./test.js", "1", "5", "lint/test", "error", "Test error"],
        ["./src/utils.js", "10", "15", "lint/warning", "warning", "Test warning"],
    ]
    assert_that(rows).is_equal_to(expected)


def test_format_biome_issues_empty() -> None:
    """Test formatting empty issues list."""
    result = format_biome_issues([])
    assert_that(result).is_equal_to("No issues found.")


def test_format_biome_issues_json_format() -> None:
    """Test formatting issues in JSON format."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/test",
            severity="error",
            message="Test error",
            fixable=True,
        ),
    ]

    result = format_biome_issues(issues, format="json")
    # JSON format should return raw table data, not split by fixability
    assert_that(result).contains("test.js")
    assert_that(result).contains("lint/test")


def test_format_biome_issues_grid_format_fixable_only() -> None:
    """Test formatting issues in grid format with only fixable issues."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/fixable",
            severity="error",
            message="Fixable error",
            fixable=True,
        ),
    ]

    result = format_biome_issues(issues, format="grid")
    assert_that(result).contains("Auto-fixable issues")
    assert_that(result).contains("test.js")
    assert_that(result).contains("Fixable error")
    # Since all issues are fixable, there should be no "Not auto-fixable issues" section
    assert_that(result).does_not_contain("Not auto-fixable issues")


def test_format_biome_issues_grid_format_non_fixable_only() -> None:
    """Test formatting issues in grid format with only non-fixable issues."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/not_fixable",
            severity="error",
            message="Not fixable error",
            fixable=False,
        ),
    ]

    result = format_biome_issues(issues, format="grid")
    assert_that(result).contains("Not auto-fixable issues")
    assert_that(result).contains("test.js")
    assert_that(result).contains("Not fixable error")
    # Since all issues are non-fixable, there should be no "Auto-fixable issues" section
    assert_that(result).does_not_contain("Auto-fixable issues")


def test_format_biome_issues_grid_format_mixed() -> None:
    """Test formatting issues in grid format with mixed fixable/non-fixable issues."""
    issues = [
        BiomeIssue(
            file="fixable.js",
            line=1,
            column=5,
            code="lint/fixable",
            severity="error",
            message="Fixable error",
            fixable=True,
        ),
        BiomeIssue(
            file="not_fixable.js",
            line=2,
            column=10,
            code="lint/not_fixable",
            severity="warning",
            message="Not fixable warning",
            fixable=False,
        ),
    ]

    result = format_biome_issues(issues, format="grid")
    assert_that(result).contains("Auto-fixable issues")
    assert_that(result).contains("fixable.js")
    assert_that(result).contains("Fixable error")
    assert_that(result).contains("Not auto-fixable issues")
    assert_that(result).contains("not_fixable.js")
    assert_that(result).contains("Not fixable warning")


def test_format_biome_issues_markdown_format() -> None:
    """Test formatting issues in markdown format."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/test",
            severity="error",
            message="Test error",
            fixable=True,
        ),
    ]

    result = format_biome_issues(issues, format="markdown")
    assert_that(result).contains("Auto-fixable issues")
    assert_that(result).contains("test.js")


def test_format_biome_issues_unknown_format() -> None:
    """Test formatting issues with unknown format falls back to grid."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            code="lint/test",
            severity="error",
            message="Test error",
            fixable=True,
        ),
    ]

    result = format_biome_issues(issues, format="unknown")
    # Should fall back to grid format
    assert_that(result).contains("Auto-fixable issues")


def test_format_biome_issues_with_end_positions() -> None:
    """Test formatting issues that include end line/column positions."""
    issues = [
        BiomeIssue(
            file="test.js",
            line=1,
            column=5,
            end_line=1,
            end_column=10,
            code="lint/test",
            severity="error",
            message="Test error with range",
            fixable=False,
        ),
    ]

    result = format_biome_issues(issues, format="grid")
    assert_that(result).contains("test.js")
    assert_that(result).contains("Test error with range")
