"""Unit tests for shfmt parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.shfmt.shfmt_parser import parse_shfmt_output


@pytest.mark.parametrize(
    "output",
    [
        None,
        "",
        "   \n  \n   ",
    ],
    ids=["none", "empty", "whitespace_only"],
)
def test_parse_shfmt_output_returns_empty_for_no_content(
    output: str | None,
) -> None:
    """Parse empty, None, or whitespace-only output returns empty list.

    Args:
        output: The shfmt output to parse.
    """
    result = parse_shfmt_output(output)
    assert_that(result).is_empty()


def test_parse_shfmt_output_single_file_diff() -> None:
    """Parse a single file diff output into one issue."""
    output = """--- script.sh.orig
+++ script.sh
@@ -1,3 +1,3 @@
-if [  "$foo" = "bar" ]; then
+if [ "$foo" = "bar" ]; then
   echo "match"
 fi"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("script.sh")
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[0].message).is_equal_to("Needs formatting")
    assert_that(result[0].fixable).is_true()
    assert_that(result[0].diff_content).contains("if [  ")
    assert_that(result[0].diff_content).contains("if [ ")


def test_parse_shfmt_output_multiple_files() -> None:
    """Parse diff output with multiple files."""
    output = """--- script1.sh.orig
+++ script1.sh
@@ -1,2 +1,2 @@
-echo  "hello"
+echo "hello"
--- script2.sh.orig
+++ script2.sh
@@ -5,2 +5,2 @@
-if[  "$x" ]; then
+if [ "$x" ]; then"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(2)
    assert_that(result[0].file).is_equal_to("script1.sh")
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[1].file).is_equal_to("script2.sh")
    assert_that(result[1].line).is_equal_to(5)


def test_parse_shfmt_output_file_with_path() -> None:
    """Parse diff with directory path in filename."""
    output = """--- scripts/deploy/setup.sh.orig
+++ scripts/deploy/setup.sh
@@ -10,2 +10,2 @@
-echo  "deploying"
+echo "deploying"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("scripts/deploy/setup.sh")
    assert_that(result[0].line).is_equal_to(10)


def test_parse_shfmt_output_extracts_diff_content() -> None:
    """Verify diff content is captured correctly."""
    output = """--- test.sh.orig
+++ test.sh
@@ -1,5 +1,5 @@
 #!/bin/bash
-x=1+2
+x=1 + 2
 echo $x
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].diff_content).contains("--- test.sh.orig")
    assert_that(result[0].diff_content).contains("+++ test.sh")
    assert_that(result[0].diff_content).contains("-x=1+2")
    assert_that(result[0].diff_content).contains("+x=1 + 2")


def test_parse_shfmt_output_multiple_hunks_uses_first_line() -> None:
    """When multiple hunks exist, use the first hunk's line number."""
    output = """--- multi.sh.orig
+++ multi.sh
@@ -3,2 +3,2 @@
-echo  "first"
+echo "first"
@@ -10,2 +10,2 @@
-echo  "second"
+echo "second"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    # Should use line 3 from first hunk
    assert_that(result[0].line).is_equal_to(3)


def test_parse_shfmt_output_column_is_zero() -> None:
    """Column is always 0 (shfmt doesn't provide column info)."""
    output = """--- test.sh.orig
+++ test.sh
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result[0].column).is_equal_to(0)


def test_parse_shfmt_output_fixable_is_true() -> None:
    """All shfmt issues are fixable."""
    output = """--- test.sh.orig
+++ test.sh
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result[0].fixable).is_true()


def test_parse_shfmt_output_no_orig_suffix() -> None:
    """Handle diff output without .orig suffix on --- line."""
    output = """--- test.sh
+++ test.sh
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test.sh")


# =============================================================================
# Edge case tests
# =============================================================================


def test_parse_shfmt_output_unicode_in_content() -> None:
    """Handle Unicode characters in diff content."""
    output = """--- unicode.sh.orig
+++ unicode.sh
@@ -1 +1 @@
-echo  "Olá mundo"
+echo "Olá mundo"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].diff_content).contains("Olá")


def test_parse_shfmt_output_file_path_with_spaces() -> None:
    """Handle file paths with spaces."""
    output = """--- my scripts/test.sh.orig
+++ my scripts/test.sh
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("my scripts/test.sh")


def test_parse_shfmt_output_very_large_line_number() -> None:
    """Handle very large line numbers."""
    output = """--- large.sh.orig
+++ large.sh
@@ -999999 +999999 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(999999)


def test_parse_shfmt_output_deeply_nested_path() -> None:
    """Handle deeply nested file paths."""
    deep_path = "a/b/c/d/e/f/g/h/i/j/script.sh"
    output = f"""--- {deep_path}.orig
+++ {deep_path}
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to(deep_path)


def test_parse_shfmt_output_special_chars_in_content() -> None:
    """Handle special characters in diff content."""
    output = """--- special.sh.orig
+++ special.sh
@@ -1 +1 @@
-echo  '$var' && echo "quote: \"nested\""
+echo '$var' && echo "quote: \"nested\""
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].diff_content).contains("$var")
    assert_that(result[0].diff_content).contains("nested")


def test_parse_shfmt_output_empty_hunk() -> None:
    """Handle diff with context-only hunk (no changes)."""
    # This is an edge case - shfmt wouldn't normally output this,
    # but parser should handle it gracefully
    output = """--- test.sh.orig
+++ test.sh
@@ -1,3 +1,3 @@
 #!/bin/bash
 echo "unchanged"
 exit 0
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test.sh")
    # Line defaults to 1 from the hunk header (fallback behavior)
    assert_that(result[0].line).is_equal_to(1)


def test_parse_shfmt_output_bash_extension() -> None:
    """Parse file with .bash extension."""
    output = """--- script.bash.orig
+++ script.bash
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("script.bash")


def test_parse_shfmt_output_ksh_extension() -> None:
    """Parse file with .ksh extension."""
    output = """--- script.ksh.orig
+++ script.ksh
@@ -1 +1 @@
-echo  "test"
+echo "test"
"""
    result = parse_shfmt_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("script.ksh")
