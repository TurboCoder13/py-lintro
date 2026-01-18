"""Unit tests for rustfmt parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.rustfmt.rustfmt_parser import parse_rustfmt_output


@pytest.mark.parametrize(
    ("output", "expected_count"),
    [
        pytest.param(None, 0, id="none_input"),
        pytest.param("", 0, id="empty_string"),
        pytest.param("   \n\n  ", 0, id="whitespace_only"),
    ],
)
def test_parse_rustfmt_output_empty_cases(
    output: str | None,
    expected_count: int,
) -> None:
    """Parser returns empty list for empty/None input.

    Args:
        output: The input to parse.
        expected_count: Expected number of issues.
    """
    result = parse_rustfmt_output(output)
    assert_that(result).is_length(expected_count)


def test_parse_rustfmt_output_diff_format() -> None:
    """Parser extracts issues from diff-style output."""
    output = """Diff in src/main.rs at line 5:
 fn main() {
-    println!("hello");
+    println!("hello");
 }
"""
    result = parse_rustfmt_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.rs")
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[0].message).is_equal_to("File needs formatting")
    assert_that(result[0].fixable).is_true()


def test_parse_rustfmt_output_multiple_diffs() -> None:
    """Parser handles multiple diff sections."""
    output = """Diff in src/main.rs at line 5:
 fn main() {
-    let x=1;
+    let x = 1;
 }
Diff in src/lib.rs at line 10:
 fn foo() {
-    bar()
+    bar();
 }
"""
    result = parse_rustfmt_output(output)

    # Parser deduplicates by file, so each file only appears once
    assert_that(result).is_length(2)
    assert_that(result[0].file).is_equal_to("src/main.rs")
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[1].file).is_equal_to("src/lib.rs")
    assert_that(result[1].line).is_equal_to(10)


def test_parse_rustfmt_output_standalone_file_paths() -> None:
    """Parser handles standalone .rs file paths."""
    output = """src/main.rs
src/lib.rs"""
    result = parse_rustfmt_output(output)

    assert_that(result).is_length(2)
    assert_that(result[0].file).is_equal_to("src/main.rs")
    assert_that(result[1].file).is_equal_to("src/lib.rs")


def test_parse_rustfmt_output_deduplicates_files() -> None:
    """Parser deduplicates issues by file path."""
    output = """Diff in src/main.rs at line 5:
- old
+ new
Diff in src/main.rs at line 10:
- another old
+ another new
"""
    result = parse_rustfmt_output(output)

    # Only one issue per file
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.rs")


def test_parse_rustfmt_output_mixed_content() -> None:
    """Parser handles mixed diff and other output."""
    output = """Checking src/main.rs...
Diff in src/main.rs at line 5:
 fn main() {
-    let x=1;
+    let x = 1;
 }
Some other output line
"""
    result = parse_rustfmt_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.rs")


def test_parse_rustfmt_output_no_issues() -> None:
    """Parser returns empty list for clean output."""
    output = "All checks passed!"
    result = parse_rustfmt_output(output)

    assert_that(result).is_length(0)
