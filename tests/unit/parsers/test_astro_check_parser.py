"""Unit tests for astro-check parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.astro_check.astro_check_issue import AstroCheckIssue
from lintro.parsers.astro_check.astro_check_parser import parse_astro_check_output


def test_parse_astro_check_output_empty() -> None:
    """Handle empty output."""
    assert_that(parse_astro_check_output("")).is_empty()
    assert_that(parse_astro_check_output("   \n\n  ")).is_empty()


def test_parse_astro_check_output_single_error() -> None:
    """Parse a single astro check error from text output."""
    output = "src/pages/index.astro:10:5 - error ts2322: Type 'string' is not assignable to type 'number'."
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].code).is_equal_to("TS2322")
    assert_that(issues[0].severity).is_equal_to("error")
    assert_that(issues[0].message).contains("not assignable")


def test_parse_astro_check_output_multiple_errors() -> None:
    """Parse multiple errors from astro check output."""
    output = """src/pages/index.astro:10:5 - error ts2322: Type 'string' is not assignable to type 'number'.
src/pages/about.astro:15:10 - error ts2339: Property 'foo' does not exist on type 'Bar'.
src/components/Card.astro:3:1 - warning ts6133: 'x' is declared but its value is never read."""
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(3)
    assert_that(issues[0].code).is_equal_to("TS2322")
    assert_that(issues[1].code).is_equal_to("TS2339")
    assert_that(issues[2].code).is_equal_to("TS6133")
    assert_that(issues[2].severity).is_equal_to("warning")


def test_parse_astro_check_output_tsc_style() -> None:
    """Parse tsc-style output format (parentheses)."""
    output = "src/pages/index.astro(10,5): error TS2322: Type 'string' is not assignable to type 'number'."
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].code).is_equal_to("TS2322")


def test_parse_astro_check_output_simple_format() -> None:
    """Parse simple format without severity or code."""
    output = (
        "src/pages/index.astro:10:5 Type 'string' is not assignable to type 'number'."
    )
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].message).contains("not assignable")


def test_parse_astro_check_output_windows_paths() -> None:
    """Normalize Windows backslashes to forward slashes."""
    output = r"src\pages\index.astro:10:5 - error ts2322: Type mismatch."
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")


def test_parse_astro_check_output_ansi_codes() -> None:
    """Strip ANSI escape codes from output."""
    # Simulated ANSI color codes around file path
    output = "\x1b[31msrc/pages/index.astro:10:5 - error ts2322: Type mismatch.\x1b[0m"
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")


def test_parse_astro_check_output_skips_noise_lines() -> None:
    """Skip non-error lines like summary and progress."""
    output = """Checking project...
Result: 2 errors
src/pages/index.astro:10:5 - error ts2322: Type mismatch.
Found 1 error in 1 file."""
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/pages/index.astro")


def test_parse_astro_check_output_hint_severity() -> None:
    """Parse hint severity level."""
    output = "src/pages/index.astro:10:5 - hint ts80001: Use optional chaining."
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("hint")


def test_astro_check_issue_type() -> None:
    """Verify parsed issues are AstroCheckIssue instances."""
    output = "src/pages/index.astro:10:5 - error ts2322: Type error."
    issues = parse_astro_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0]).is_instance_of(AstroCheckIssue)
