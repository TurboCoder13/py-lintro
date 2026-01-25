"""Tests for pydoclint parser edge cases."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output


def test_parse_unicode_path() -> None:
    """Parse issue with unicode characters in path."""
    output = """src/模块/helper.py
    10: DOC101: Test message"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/模块/helper.py")


def test_parse_path_with_spaces() -> None:
    """Parse issue with spaces in file path.

    Note: pydoclint file path pattern requires the path to end with .py/.pyi.
    Paths with spaces are preserved as-is.
    """
    output = """src/my module/helper file.py
    10: DOC101: Test message"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/my module/helper file.py")


def test_parse_message_with_special_characters() -> None:
    """Parse issue with special characters in message."""
    output = """test.py
    10: DOC101: Function `foo` has 'special' chars: [a, b]"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).is_equal_to(
        "Function `foo` has 'special' chars: [a, b]",
    )


def test_parse_very_long_message() -> None:
    """Parse issue with very long message."""
    long_message = "A" * 1000
    output = f"""test.py
    10: DOC101: {long_message}"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).is_equal_to(long_message)


def test_parse_high_line_numbers() -> None:
    """Parse issue with high line numbers.

    Note: pydoclint doesn't provide column information, so column is always 0.
    """
    output = """test.py
    99999: DOC101: Test message"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(99999)
    assert_that(result[0].column).is_equal_to(0)  # pydoclint doesn't report columns


def test_parse_windows_path() -> None:
    """Parse issue with Windows-style path (forward slashes preserved)."""
    # pydoclint typically outputs forward slashes even on Windows
    output = """src/module/test.py
    10: DOC101: Test message"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/module/test.py")


def test_parse_multiple_colons_in_message() -> None:
    """Parse issue with colons in the message."""
    output = """test.py
    10: DOC101: Error: Function `foo`: missing args: [x, y]"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).is_equal_to(
        "Error: Function `foo`: missing args: [x, y]",
    )


def test_parse_empty_lines_between_issues() -> None:
    """Parse output with empty lines between issues."""
    output = """test.py
    10: DOC101: First issue

    20: DOC201: Second issue

"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(2)
    assert_that(result[0].code).is_equal_to("DOC101")
    assert_that(result[1].code).is_equal_to("DOC201")


def test_parse_multiple_files() -> None:
    """Parse output with issues from multiple files."""
    output = """src/module_a.py
    10: DOC101: First issue
    20: DOC102: Second issue
src/module_b.py
    5: DOC201: Third issue"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(3)
    assert_that(result[0].file).is_equal_to("src/module_a.py")
    assert_that(result[1].file).is_equal_to("src/module_a.py")
    assert_that(result[2].file).is_equal_to("src/module_b.py")
