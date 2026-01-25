"""Unit tests for tsc parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.tsc.tsc_parser import parse_tsc_output


def test_parse_tsc_output_single_error() -> None:
    """Parse a single tsc error from text output."""
    output = "src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'."
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/main.ts")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].code).is_equal_to("TS2322")
    assert_that(issues[0].severity).is_equal_to("error")
    assert_that(issues[0].message).contains("not assignable")


def test_parse_tsc_output_single_warning() -> None:
    """Parse a single tsc warning from text output."""
    output = "src/utils.ts(15,1): warning TS6133: 'x' is declared but its value is never read."
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("warning")
    assert_that(issues[0].code).is_equal_to("TS6133")


def test_parse_tsc_output_multiple_errors() -> None:
    """Parse multiple errors from tsc output."""
    output = """src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
src/main.ts(15,10): error TS2339: Property 'foo' does not exist on type 'Bar'.
src/utils.ts(3,1): warning TS6133: 'x' is declared but its value is never read."""
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(3)
    assert_that(issues[0].code).is_equal_to("TS2322")
    assert_that(issues[1].code).is_equal_to("TS2339")
    assert_that(issues[2].code).is_equal_to("TS6133")
    assert_that(issues[2].severity).is_equal_to("warning")


def test_parse_tsc_output_mixed_with_non_errors() -> None:
    """Parse errors mixed with non-error output lines."""
    output = """Starting compilation...
src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
Processing files...
src/utils.ts(3,1): error TS2304: Cannot find name 'foo'.
Found 2 errors."""
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("src/main.ts")
    assert_that(issues[1].file).is_equal_to("src/utils.ts")


def test_parse_tsc_output_empty() -> None:
    """Handle empty output."""
    assert_that(parse_tsc_output("")).is_empty()
    assert_that(parse_tsc_output("   \n\n  ")).is_empty()


def test_parse_tsc_output_windows_paths() -> None:
    """Normalize Windows backslashes to forward slashes."""
    output = r"src\components\Button.tsx(10,5): error TS2322: Type mismatch."
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/components/Button.tsx")


def test_parse_tsc_output_tsx_files() -> None:
    """Parse errors from TSX files."""
    output = (
        "src/components/Button.tsx(25,12): error TS2769: No overload matches this call."
    )
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/components/Button.tsx")


def test_parse_tsc_output_mts_cts_files() -> None:
    """Parse errors from .mts and .cts files."""
    output = """src/module.mts(5,1): error TS2322: Type error.
src/common.cts(10,1): error TS2322: Type error."""
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("src/module.mts")
    assert_that(issues[1].file).is_equal_to("src/common.cts")


def test_parse_tsc_output_deep_nested_path() -> None:
    """Parse errors with deeply nested file paths."""
    output = "packages/app/src/features/auth/hooks/useAuth.ts(42,15): error TS2345: Argument type mismatch."
    issues = parse_tsc_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to(
        "packages/app/src/features/auth/hooks/useAuth.ts",
    )


def test_parse_tsc_output_invalid_json() -> None:
    """Skip non-matching lines gracefully."""
    output = """Starting compilation...
not valid tsc output
error TS6053: File not found."""
    issues = parse_tsc_output(output)

    assert_that(issues).is_empty()


# Tests for TscIssue.to_display_row


def test_tsc_issue_to_display_row() -> None:
    """Convert TscIssue to display row format."""
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


def test_tsc_issue_to_display_row_minimal() -> None:
    """Convert minimal TscIssue to display row format."""
    from lintro.parsers.tsc.tsc_issue import TscIssue

    issue = TscIssue(file="main.ts", line=1, column=1, message="Error")
    row = issue.to_display_row()

    assert_that(row["file"]).is_equal_to("main.ts")
    assert_that(row["code"]).is_equal_to("")
    assert_that(row["severity"]).is_equal_to("")
