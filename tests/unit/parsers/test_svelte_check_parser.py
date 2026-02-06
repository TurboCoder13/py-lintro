"""Unit tests for svelte-check parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.svelte_check.svelte_check_issue import SvelteCheckIssue
from lintro.parsers.svelte_check.svelte_check_parser import parse_svelte_check_output


def test_parse_svelte_check_output_empty() -> None:
    """Handle empty output."""
    assert_that(parse_svelte_check_output("")).is_empty()
    assert_that(parse_svelte_check_output("   \n\n  ")).is_empty()


def test_parse_svelte_check_output_machine_verbose_single_error() -> None:
    """Parse a single machine-verbose error."""
    output = "src/lib/Button.svelte:15:5:15:10 Error Type 'string' is not assignable to type 'number'."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/lib/Button.svelte")
    assert_that(issues[0].line).is_equal_to(15)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].severity).is_equal_to("error")
    assert_that(issues[0].message).contains("not assignable")


def test_parse_svelte_check_output_multiple_errors() -> None:
    """Parse multiple errors from svelte-check output."""
    output = """src/lib/Button.svelte:15:5:15:10 Error Type 'string' is not assignable to type 'number'.
src/routes/+page.svelte:20:3:20:15 Error Property 'foo' does not exist on type 'Bar'.
src/lib/Card.svelte:8:1:8:20 Warning Unused CSS selector '.unused'."""
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(3)
    assert_that(issues[0].severity).is_equal_to("error")
    assert_that(issues[1].severity).is_equal_to("error")
    assert_that(issues[2].severity).is_equal_to("warning")


def test_parse_svelte_check_output_machine_format() -> None:
    """Parse machine format (non-verbose)."""
    output = "ERROR src/lib/Button.svelte:15:5 Type 'string' is not assignable to type 'number'."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/lib/Button.svelte")
    assert_that(issues[0].line).is_equal_to(15)
    assert_that(issues[0].column).is_equal_to(5)
    assert_that(issues[0].severity).is_equal_to("error")


def test_parse_svelte_check_output_warning_severity() -> None:
    """Parse warning severity level."""
    output = "src/lib/Card.svelte:8:1:8:20 Warning Unused CSS selector '.unused'."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("warning")


def test_parse_svelte_check_output_hint_severity() -> None:
    """Parse hint severity level."""
    output = (
        "src/lib/Card.svelte:8:1:8:20 Hint Consider using a more specific selector."
    )
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("hint")


def test_parse_svelte_check_output_windows_paths() -> None:
    """Normalize Windows backslashes to forward slashes."""
    output = r"src\lib\Button.svelte:15:5:15:10 Error Type mismatch."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/lib/Button.svelte")


def test_parse_svelte_check_output_ansi_codes() -> None:
    """Strip ANSI escape codes from output."""
    output = "\x1b[31msrc/lib/Button.svelte:15:5:15:10 Error Type mismatch.\x1b[0m"
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/lib/Button.svelte")


def test_parse_svelte_check_output_skips_noise_lines() -> None:
    """Skip non-error lines like summary and progress."""
    output = """====================================
Loading svelte-check in workspace...
Diagnostics:
src/lib/Button.svelte:15:5:15:10 Error Type mismatch.
svelte-check found 1 error"""
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("src/lib/Button.svelte")


def test_parse_svelte_check_output_end_line_different() -> None:
    """Parse issue spanning multiple lines."""
    output = "src/lib/Button.svelte:15:5:18:10 Error Multi-line type error."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].end_line).is_equal_to(18)
    assert_that(issues[0].end_column).is_equal_to(10)


def test_parse_svelte_check_output_same_line_same_column() -> None:
    """End line/column set to None when same as start."""
    output = "src/lib/Button.svelte:15:5:15:5 Error Point error."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].end_line).is_none()
    assert_that(issues[0].end_column).is_none()


def test_parse_svelte_check_output_warn_machine_format() -> None:
    """Parse WARN severity in machine format."""
    output = "WARN src/lib/Card.svelte:8:1 Unused CSS selector."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("warning")


def test_parse_svelte_check_output_hint_machine_format() -> None:
    """Parse HINT severity in machine format."""
    output = "HINT src/lib/Card.svelte:8:1 Consider refactoring."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].severity).is_equal_to("hint")


def test_svelte_check_issue_type() -> None:
    """Verify parsed issues are SvelteCheckIssue instances."""
    output = "src/lib/Button.svelte:15:5:15:10 Error Type error."
    issues = parse_svelte_check_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0]).is_instance_of(SvelteCheckIssue)
