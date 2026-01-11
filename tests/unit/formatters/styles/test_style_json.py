"""Unit tests for JsonStyle formatter.

Tests verify JsonStyle correctly formats tabular data as valid JSON
with proper structure, metadata, and column normalization.
"""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.formatters.styles.json import JsonStyle

from .conftest import MULTI_ROW_DATA, SINGLE_ROW_DATA, STANDARD_COLUMNS, TWO_COLUMNS


def test_json_style_empty_rows_produces_valid_json(json_style: JsonStyle) -> None:
    """JsonStyle formats empty rows as valid JSON with expected structure.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(TWO_COLUMNS, [], tool_name="ruff")
    data = json.loads(result)

    assert_that(data["tool"]).is_equal_to("ruff")
    assert_that(data["total_issues"]).is_equal_to(0)
    assert_that(data["issues"]).is_empty()


def test_json_style_single_row_produces_correct_structure(
    json_style: JsonStyle,
) -> None:
    """JsonStyle formats single row as JSON with correct issue structure.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(
        STANDARD_COLUMNS,
        SINGLE_ROW_DATA,
        tool_name="mypy",
    )
    data = json.loads(result)

    assert_that(data["tool"]).is_equal_to("mypy")
    assert_that(data["total_issues"]).is_equal_to(1)
    assert_that(data["issues"]).is_length(1)
    assert_that(data["issues"][0]["file"]).is_equal_to("src/main.py")
    assert_that(data["issues"][0]["line"]).is_equal_to("10")
    assert_that(data["issues"][0]["message"]).is_equal_to("Error found")


def test_json_style_multiple_rows_counts_correctly(json_style: JsonStyle) -> None:
    """JsonStyle formats multiple rows with correct count.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(TWO_COLUMNS, MULTI_ROW_DATA, tool_name="ruff")
    data = json.loads(result)

    assert_that(data["total_issues"]).is_equal_to(2)
    assert_that(data["issues"]).is_length(2)


def test_json_style_column_name_normalization(json_style: JsonStyle) -> None:
    """JsonStyle normalizes column names to lowercase with underscores.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(
        ["File Path", "Line Number"],
        [["src/main.py", "10"]],
    )
    data = json.loads(result)

    assert_that(data["issues"][0]).contains_key("file_path")
    assert_that(data["issues"][0]).contains_key("line_number")


def test_json_style_with_metadata(json_style: JsonStyle) -> None:
    """JsonStyle includes provided metadata in output.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(
        TWO_COLUMNS,
        [["src/main.py", "10"]],
        tool_name="ruff",
        metadata={"version": "1.0.0"},
    )
    data = json.loads(result)

    assert_that(data["metadata"]["version"]).is_equal_to("1.0.0")


def test_json_style_with_extra_kwargs_in_metadata(json_style: JsonStyle) -> None:
    """JsonStyle includes extra kwargs as metadata.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(
        TWO_COLUMNS,
        [["src/main.py", "10"]],
        tool_name="ruff",
        custom_field="custom_value",
    )
    data = json.loads(result)

    assert_that(data["metadata"]["custom_field"]).is_equal_to("custom_value")


def test_json_style_has_timestamp(json_style: JsonStyle) -> None:
    """JsonStyle output includes timestamp field.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(["File"], [["src/main.py"]])
    data = json.loads(result)

    assert_that(data).contains_key("timestamp")


def test_json_style_row_shorter_than_columns(json_style: JsonStyle) -> None:
    """JsonStyle handles row with fewer elements than columns.

    Args:
        json_style: The JsonStyle formatter instance.
    """
    result = json_style.format(STANDARD_COLUMNS, [["src/main.py"]])
    data = json.loads(result)

    assert_that(data["issues"][0]["file"]).is_equal_to("src/main.py")
    assert_that(data["issues"][0]).does_not_contain_key("line")
