"""Unit tests for tsc parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.tsc.tsc_parser import (
    TSC_ISSUE_PATTERN,
    _parse_line,
    parse_tsc_output,
)


class TestTscIssuePattern:
    """Tests for TSC_ISSUE_PATTERN regex."""

    def test_matches_error(self) -> None:
        """Match standard error output format."""
        line = (
            "src/main.ts(10,5): error TS2322: "
            "Type 'string' is not assignable to type 'number'."
        )
        match = TSC_ISSUE_PATTERN.match(line)
        assert match is not None
        assert_that(match.group("file")).is_equal_to("src/main.ts")
        assert_that(match.group("line")).is_equal_to("10")
        assert_that(match.group("column")).is_equal_to("5")
        assert_that(match.group("severity")).is_equal_to("error")
        assert_that(match.group("code")).is_equal_to("TS2322")

    def test_matches_warning(self) -> None:
        """Match warning output format."""
        line = (
            "src/utils.ts(15,1): warning TS6133: "
            "'x' is declared but its value is never read."
        )
        match = TSC_ISSUE_PATTERN.match(line)
        assert match is not None
        assert_that(match.group("severity")).is_equal_to("warning")
        assert_that(match.group("code")).is_equal_to("TS6133")

    def test_matches_windows_path(self) -> None:
        """Match Windows-style paths with backslashes."""
        line = r"src\components\Button.tsx(25,10): error TS2339: Property 'foo' does not exist."
        match = TSC_ISSUE_PATTERN.match(line)
        assert match is not None
        assert_that(match.group("file")).is_equal_to(r"src\components\Button.tsx")

    def test_matches_deep_nested_path(self) -> None:
        """Match deeply nested file paths."""
        line = (
            "packages/app/src/features/auth/hooks/useAuth.ts(42,15): "
            "error TS2345: Argument type mismatch."
        )
        match = TSC_ISSUE_PATTERN.match(line)
        assert match is not None
        assert_that(match.group("file")).is_equal_to(
            "packages/app/src/features/auth/hooks/useAuth.ts",
        )

    def test_no_match_for_non_tsc_output(self) -> None:
        """Not match non-tsc output."""
        lines = [
            "Starting compilation...",
            "Found 3 errors.",
            "error TS6053: File not found.",
            "",
        ]
        for line in lines:
            match = TSC_ISSUE_PATTERN.match(line)
            assert_that(match).is_none()


class TestParseLine:
    """Tests for _parse_line function."""

    def test_parse_valid_error(self) -> None:
        """Parse a valid error line."""
        line = (
            "src/index.ts(5,10): error TS2322: "
            "Type 'string' is not assignable to type 'number'."
        )
        issue = _parse_line(line)
        assert issue is not None
        assert_that(issue.file).is_equal_to("src/index.ts")
        assert_that(issue.line).is_equal_to(5)
        assert_that(issue.column).is_equal_to(10)
        assert_that(issue.code).is_equal_to("TS2322")
        assert_that(issue.severity).is_equal_to("error")
        assert_that(issue.message).is_equal_to(
            "Type 'string' is not assignable to type 'number'.",
        )

    def test_parse_valid_warning(self) -> None:
        """Parse a valid warning line."""
        line = (
            "src/utils.ts(1,7): warning TS6133: "
            "'unused' is declared but its value is never read."
        )
        issue = _parse_line(line)
        assert issue is not None
        assert_that(issue.severity).is_equal_to("warning")
        assert_that(issue.code).is_equal_to("TS6133")

    def test_parse_normalizes_windows_paths(self) -> None:
        """Normalize Windows backslashes to forward slashes."""
        line = r"src\components\Button.tsx(10,5): error TS2322: Type mismatch."
        issue = _parse_line(line)
        assert issue is not None
        assert_that(issue.file).is_equal_to("src/components/Button.tsx")

    def test_parse_empty_line_returns_none(self) -> None:
        """Return None for empty lines."""
        assert_that(_parse_line("")).is_none()
        assert_that(_parse_line("   ")).is_none()

    def test_parse_invalid_line_returns_none(self) -> None:
        """Return None for non-matching lines."""
        assert_that(_parse_line("Starting compilation...")).is_none()
        assert_that(_parse_line("Found 3 errors.")).is_none()


class TestParseTscOutput:
    """Tests for parse_tsc_output function."""

    def test_parse_empty_output(self) -> None:
        """Return empty list for empty output."""
        issues = parse_tsc_output("")
        assert_that(issues).is_empty()

    def test_parse_whitespace_output(self) -> None:
        """Return empty list for whitespace-only output."""
        issues = parse_tsc_output("   \n\n  ")
        assert_that(issues).is_empty()

    def test_parse_single_error(self) -> None:
        """Parse single error from output."""
        output = (
            "src/main.ts(10,5): error TS2322: "
            "Type 'string' is not assignable to type 'number'."
        )
        issues = parse_tsc_output(output)
        assert_that(issues).is_length(1)
        assert_that(issues[0].code).is_equal_to("TS2322")

    def test_parse_multiple_errors(self) -> None:
        """Parse multiple errors from output."""
        output = """src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
src/main.ts(15,10): error TS2339: Property 'foo' does not exist on type 'Bar'.
src/utils.ts(3,1): warning TS6133: 'x' is declared but its value is never read."""
        issues = parse_tsc_output(output)
        assert_that(issues).is_length(3)
        assert_that(issues[0].code).is_equal_to("TS2322")
        assert_that(issues[1].code).is_equal_to("TS2339")
        assert_that(issues[2].code).is_equal_to("TS6133")
        assert_that(issues[2].severity).is_equal_to("warning")

    def test_parse_mixed_output(self) -> None:
        """Parse errors mixed with non-error output."""
        output = """Starting compilation...
src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
Processing files...
src/utils.ts(3,1): error TS2304: Cannot find name 'foo'.
Found 2 errors."""
        issues = parse_tsc_output(output)
        assert_that(issues).is_length(2)
        assert_that(issues[0].file).is_equal_to("src/main.ts")
        assert_that(issues[1].file).is_equal_to("src/utils.ts")

    def test_parse_tsx_files(self) -> None:
        """Parse errors from TSX files."""
        output = (
            "src/components/Button.tsx(25,12): "
            "error TS2769: No overload matches this call."
        )
        issues = parse_tsc_output(output)
        assert_that(issues).is_length(1)
        assert_that(issues[0].file).is_equal_to("src/components/Button.tsx")

    def test_parse_mts_cts_files(self) -> None:
        """Parse errors from .mts and .cts files."""
        output = """src/module.mts(5,1): error TS2322: Type error.
src/common.cts(10,1): error TS2322: Type error."""
        issues = parse_tsc_output(output)
        assert_that(issues).is_length(2)
        assert_that(issues[0].file).is_equal_to("src/module.mts")
        assert_that(issues[1].file).is_equal_to("src/common.cts")


class TestTscIssueToDisplayRow:
    """Tests for TscIssue.to_display_row method."""

    def test_to_display_row_complete(self) -> None:
        """Convert complete issue to display row."""
        from lintro.parsers.tsc.tsc_issue import TscIssue

        issue = TscIssue(
            file="src/main.ts",
            line=10,
            column=5,
            code="TS2322",
            message="Type error",
            severity="error",
        )
        row = issue.to_display_row()
        assert_that(row["file"]).is_equal_to("src/main.ts")
        assert_that(row["line"]).is_equal_to("10")
        assert_that(row["column"]).is_equal_to("5")
        assert_that(row["code"]).is_equal_to("TS2322")
        assert_that(row["message"]).is_equal_to("Type error")
        assert_that(row["severity"]).is_equal_to("error")

    def test_to_display_row_minimal(self) -> None:
        """Convert minimal issue to display row."""
        from lintro.parsers.tsc.tsc_issue import TscIssue

        issue = TscIssue(file="main.ts", line=1, column=1, message="Error")
        row = issue.to_display_row()
        assert_that(row["file"]).is_equal_to("main.ts")
        assert_that(row["code"]).is_equal_to("")
        assert_that(row["severity"]).is_equal_to("")
