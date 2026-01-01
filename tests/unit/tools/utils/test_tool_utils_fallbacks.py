"""Cover `tool_utils` fallbacks and errors."""

from __future__ import annotations

from assertpy import assert_that

import lintro.utils.tool_utils as tu
from lintro.utils.cli_parsing import parse_tool_list


def test_format_as_table_fallback_when_no_tabulate(monkeypatch) -> None:
    """Fallback to plain text table when tabulate is unavailable.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    from lintro.utils import table_formatting

    # Force TABULATE_AVAILABLE False
    monkeypatch.setattr(table_formatting, "TABULATE_AVAILABLE", False, raising=True)
    issues = [
        {"file": "x.py", "line": 1, "column": 2, "code": "X", "message": "m"},
        {"file": "y.py", "line": 3, "column": 4, "code": "Y", "message": "n"},
    ]
    txt = tu.format_as_table(issues=issues, tool_name="unknown", group_by=None)
    assert_that(isinstance(txt, str)).is_true()
    # Fallback header may be lowercase normalized keys
    assert_that(
        ("File" in txt and "Line" in txt) or ("file" in txt and "line" in txt),
    ).is_true()


def test_parse_tool_list_error_on_bad_name() -> None:
    """Raise ValueError when parsing an unknown tool name.

    Raises:
        AssertionError: If the expected ValueError is not raised.
    """
    try:
        _ = parse_tool_list("notatool")
        raise AssertionError("Expected ValueError for bad tool name")
    except ValueError as e:  # noqa: PT017
        assert_that("Unknown core" in str(e) or "Unknown tool" in str(e)).is_true()
