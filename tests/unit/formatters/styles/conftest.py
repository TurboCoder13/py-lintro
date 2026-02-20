"""Shared fixtures and test data for formatter style tests.

Provides common fixtures for style instances and shared test data
used across multiple style test modules.
"""

from __future__ import annotations

import pytest

from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.github import GitHubStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle

# --- Style instance fixtures ---


@pytest.fixture
def plain_style() -> PlainStyle:
    """Create PlainStyle instance.

    Returns:
        A PlainStyle instance for testing.
    """
    return PlainStyle()


@pytest.fixture
def grid_style() -> GridStyle:
    """Create GridStyle instance.

    Returns:
        A GridStyle instance for testing.
    """
    return GridStyle()


@pytest.fixture
def json_style() -> JsonStyle:
    """Create JsonStyle instance.

    Returns:
        A JsonStyle instance for testing.
    """
    return JsonStyle()


@pytest.fixture
def html_style() -> HtmlStyle:
    """Create HtmlStyle instance.

    Returns:
        An HtmlStyle instance for testing.
    """
    return HtmlStyle()


@pytest.fixture
def markdown_style() -> MarkdownStyle:
    """Create MarkdownStyle instance.

    Returns:
        A MarkdownStyle instance for testing.
    """
    return MarkdownStyle()


@pytest.fixture
def csv_style() -> CsvStyle:
    """Create CsvStyle instance.

    Returns:
        A CsvStyle instance for testing.
    """
    return CsvStyle()


@pytest.fixture
def github_style() -> GitHubStyle:
    """Create GitHubStyle instance.

    Returns:
        A GitHubStyle instance for testing.
    """
    return GitHubStyle()


# --- Common test data ---

SINGLE_ROW_DATA = [["src/main.py", "10", "Error found"]]
MULTI_ROW_DATA = [
    ["src/a.py", "10"],
    ["src/b.py", "20"],
]
STANDARD_COLUMNS = ["File", "Line", "Message"]
TWO_COLUMNS = ["File", "Line"]
