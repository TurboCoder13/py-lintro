"""Unit tests for SQLFluff parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.sqlfluff.sqlfluff_parser import parse_sqlfluff_output


@pytest.mark.parametrize(
    "output",
    [
        "",
        None,
        "   \n  \n   ",
        "[]",
        "{}",
    ],
    ids=["empty", "none", "whitespace_only", "empty_array", "empty_object"],
)
def test_parse_sqlfluff_output_returns_empty_for_no_content(
    output: str | None,
) -> None:
    """Parse empty or whitespace-only output returns empty list.

    Args:
        output: The SQLFluff output to parse.
    """
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


def test_parse_sqlfluff_output_single_violation() -> None:
    """Parse single violation from SQLFluff JSON output."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "end_line_no": 1,
        "end_line_pos": 6,
        "code": "L010",
        "description": "Keywords must be upper case.",
        "name": "capitalisation.keywords"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("query.sql")
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[0].column).is_equal_to(1)
    assert_that(result[0].end_line).is_equal_to(1)
    assert_that(result[0].end_column).is_equal_to(6)
    assert_that(result[0].code).is_equal_to("L010")
    assert_that(result[0].rule_name).is_equal_to("capitalisation.keywords")
    assert_that(result[0].message).is_equal_to("Keywords must be upper case.")


def test_parse_sqlfluff_output_multiple_violations_single_file() -> None:
    """Parse multiple violations from a single file."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Keywords must be upper case.",
        "name": "capitalisation.keywords"
      },
      {
        "start_line_no": 3,
        "start_line_pos": 5,
        "code": "L011",
        "description": "Implicit aliasing not allowed.",
        "name": "aliasing.table"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(2)
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[0].code).is_equal_to("L010")
    assert_that(result[1].line).is_equal_to(3)
    assert_that(result[1].code).is_equal_to("L011")


def test_parse_sqlfluff_output_multiple_files() -> None:
    """Parse violations from multiple files."""
    output = """[
  {
    "filepath": "query1.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error 1",
        "name": "rule.one"
      }
    ]
  },
  {
    "filepath": "query2.sql",
    "violations": [
      {
        "start_line_no": 5,
        "start_line_pos": 10,
        "code": "L020",
        "description": "Error 2",
        "name": "rule.two"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(2)
    assert_that(result[0].file).is_equal_to("query1.sql")
    assert_that(result[1].file).is_equal_to("query2.sql")


def test_parse_sqlfluff_output_file_with_no_violations() -> None:
    """Parse output where a file has no violations."""
    output = """[
  {
    "filepath": "clean.sql",
    "violations": []
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


def test_parse_sqlfluff_output_mixed_files() -> None:
    """Parse output with some files having violations and some not."""
    output = """[
  {
    "filepath": "clean.sql",
    "violations": []
  },
  {
    "filepath": "dirty.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("dirty.sql")


def test_parse_sqlfluff_output_missing_optional_fields() -> None:
    """Parse violations with missing optional fields."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error message"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].end_line).is_none()
    assert_that(result[0].end_column).is_none()
    assert_that(result[0].rule_name).is_equal_to("")


def test_parse_sqlfluff_output_invalid_json() -> None:
    """Handle invalid JSON gracefully."""
    output = "not valid json"
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


def test_parse_sqlfluff_output_not_a_list() -> None:
    """Handle non-list JSON gracefully."""
    output = '{"filepath": "query.sql"}'
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


# =============================================================================
# Edge case tests
# =============================================================================


def test_parse_sqlfluff_output_unicode_in_message() -> None:
    """Handle Unicode characters in error messages."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Palavras-chave devem estar em maiusculas",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("Palavras-chave")


def test_parse_sqlfluff_output_file_path_with_spaces() -> None:
    """Handle file paths with spaces."""
    output = """[
  {
    "filepath": "my project/sql files/query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).contains("my project")


def test_parse_sqlfluff_output_deeply_nested_path() -> None:
    """Handle deeply nested file paths."""
    deep_path = "a/b/c/d/e/f/g/h/i/j/query.sql"
    output = f"""[
  {{
    "filepath": "{deep_path}",
    "violations": [
      {{
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error",
        "name": "rule.name"
      }}
    ]
  }}
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to(deep_path)


def test_parse_sqlfluff_output_very_large_line_number() -> None:
    """Handle very large line numbers."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 999999,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(999999)


def test_parse_sqlfluff_output_very_long_message() -> None:
    """Handle extremely long error messages."""
    long_message = "x" * 5000
    output = f"""[
  {{
    "filepath": "query.sql",
    "violations": [
      {{
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "{long_message}",
        "name": "rule.name"
      }}
    ]
  }}
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(len(result[0].message)).is_equal_to(5000)


def test_parse_sqlfluff_output_special_chars_in_message() -> None:
    """Handle special characters in error messages."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 1,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Use \\"quotes\\" and <brackets>",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("quotes")
    assert_that(result[0].message).contains("<brackets>")


def test_parse_sqlfluff_output_zero_line_number() -> None:
    """Handle zero line number (edge case)."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": [
      {
        "start_line_no": 0,
        "start_line_pos": 1,
        "code": "L010",
        "description": "Error",
        "name": "rule.name"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(0)


def test_parse_sqlfluff_output_null_violations() -> None:
    """Handle null violations array gracefully."""
    output = """[
  {
    "filepath": "query.sql",
    "violations": null
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


def test_parse_sqlfluff_output_missing_violations_key() -> None:
    """Handle missing violations key gracefully."""
    output = """[
  {
    "filepath": "query.sql"
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_empty()


def test_parse_sqlfluff_output_alternative_field_names() -> None:
    """Parse output with alternative field name mappings."""
    output = """[
  {
    "file": "query.sql",
    "violations": [
      {
        "line": 5,
        "column": 10,
        "code": "L010",
        "message": "Alternative message format",
        "rule_name": "alternative.rule"
      }
    ]
  }
]"""
    result = parse_sqlfluff_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("query.sql")
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[0].column).is_equal_to(10)
    assert_that(result[0].message).is_equal_to("Alternative message format")
    assert_that(result[0].rule_name).is_equal_to("alternative.rule")
