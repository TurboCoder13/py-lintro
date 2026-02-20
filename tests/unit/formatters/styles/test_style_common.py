"""Cross-style parametrized tests for formatter styles.

Tests common behaviors across all formatter styles using parametrization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.github import GitHubStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle

from .conftest import TWO_COLUMNS

if TYPE_CHECKING:
    from lintro.formatters.styles.base import BaseStyle


@pytest.mark.parametrize(
    ("style_class", "expected"),
    [
        pytest.param(PlainStyle, "No issues found.", id="plain"),
        pytest.param(GridStyle, "", id="grid"),
        pytest.param(HtmlStyle, "<p>No issues found.</p>", id="html"),
        pytest.param(MarkdownStyle, "No issues found.", id="markdown"),
        pytest.param(CsvStyle, "", id="csv"),
        pytest.param(GitHubStyle, "", id="github"),
    ],
)
def test_empty_rows_returns_expected_output(
    style_class: type[BaseStyle],
    expected: str,
) -> None:
    """Style returns appropriate output for empty rows.

    Args:
        style_class: The style class to test.
        expected: The expected output string.
    """
    style = style_class()
    result = style.format(TWO_COLUMNS, [])
    assert_that(result).is_equal_to(expected)
