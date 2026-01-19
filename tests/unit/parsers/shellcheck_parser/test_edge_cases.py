"""Tests for shellcheck parser edge cases."""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output

from .conftest import make_issue, make_shellcheck_output


def test_parse_unicode_in_message() -> None:
    """Handle Unicode characters in error messages."""
    output = make_shellcheck_output(
        [
            make_issue(message="Mensagem com acentos: café"),
        ],
    )
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("café")


def test_parse_file_with_path() -> None:
    """Parse file with directory path."""
    output = make_shellcheck_output(
        [
            make_issue(file="scripts/deploy/prod.sh"),
        ],
    )
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("scripts/deploy/prod.sh")


def test_parse_very_long_message() -> None:
    """Handle extremely long error messages."""
    long_text = "x" * 5000
    output = make_shellcheck_output([make_issue(message=long_text)])
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(len(result[0].message)).is_equal_to(5000)


def test_parse_very_large_line_number() -> None:
    """Handle very large line numbers."""
    output = make_shellcheck_output([make_issue(line=999999)])
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(999999)


def test_parse_special_chars_in_message() -> None:
    """Handle special characters in error messages."""
    output = make_shellcheck_output(
        [
            make_issue(message='Use "$var" instead of $var for safety.'),
        ],
    )
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).contains('"$var"')


def test_parse_deeply_nested_path() -> None:
    """Handle deeply nested file paths."""
    deep_path = "a/b/c/d/e/f/g/h/i/j/script.sh"
    output = make_shellcheck_output([make_issue(file=deep_path)])
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to(deep_path)


def test_parse_missing_required_fields_uses_defaults() -> None:
    """Parse handles missing fields with defaults."""
    data = [
        {
            "level": "warning",
            "code": 2086,
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("")
    assert_that(result[0].line).is_equal_to(0)
    assert_that(result[0].column).is_equal_to(0)
    assert_that(result[0].message).is_equal_to("")
