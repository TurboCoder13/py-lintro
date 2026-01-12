"""Tests for lintro.formatters.styles.json module."""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.formatters.styles.json import JsonStyle


def test_json_style_basic_format(json_style: JsonStyle) -> None:
    """JsonStyle formats data as valid JSON.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
        tool_name="ruff",
    )
    parsed = json.loads(result)
    assert_that(parsed).contains_key("tool")
    assert_that(parsed).contains_key("timestamp")
    assert_that(parsed).contains_key("total_issues")
    assert_that(parsed).contains_key("issues")


def test_json_style_includes_tool_name(json_style: JsonStyle) -> None:
    """JsonStyle includes tool name in output.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File"],
        [["test.py"]],
        tool_name="mypy",
    )
    parsed = json.loads(result)
    assert_that(parsed["tool"]).is_equal_to("mypy")


def test_json_style_normalizes_column_names(json_style: JsonStyle) -> None:
    """JsonStyle normalizes column names to lowercase with underscores.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File Path", "Line Number"],
        [["test.py", "10"]],
    )
    parsed = json.loads(result)
    issue = parsed["issues"][0]
    assert_that(issue).contains_key("file_path")
    assert_that(issue).contains_key("line_number")


def test_json_style_counts_issues(json_style: JsonStyle) -> None:
    """JsonStyle counts total issues correctly.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File"],
        [["a.py"], ["b.py"], ["c.py"]],
    )
    parsed = json.loads(result)
    assert_that(parsed["total_issues"]).is_equal_to(3)


def test_json_style_empty_rows(json_style: JsonStyle) -> None:
    """JsonStyle handles empty rows.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(["File"], [])
    parsed = json.loads(result)
    assert_that(parsed["total_issues"]).is_equal_to(0)
    assert_that(parsed["issues"]).is_empty()


def test_json_style_includes_metadata(json_style: JsonStyle) -> None:
    """JsonStyle includes metadata when provided.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File"],
        [["test.py"]],
        metadata={"version": "1.0"},
    )
    parsed = json.loads(result)
    assert_that(parsed).contains_key("metadata")
    assert_that(parsed["metadata"]["version"]).is_equal_to("1.0")


def test_json_style_extra_kwargs_as_metadata(json_style: JsonStyle) -> None:
    """JsonStyle adds extra kwargs to metadata.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(
        ["File"],
        [["test.py"]],
        extra_field="value",
    )
    parsed = json.loads(result)
    assert_that(parsed).contains_key("metadata")
    assert_that(parsed["metadata"]["extra_field"]).is_equal_to("value")


def test_json_style_has_timestamp(json_style: JsonStyle) -> None:
    """JsonStyle includes timestamp in output.

    Args:
        json_style: JsonStyle fixture.
    """
    result = json_style.format(["File"], [["test.py"]])
    parsed = json.loads(result)
    assert_that(parsed["timestamp"]).is_not_empty()
