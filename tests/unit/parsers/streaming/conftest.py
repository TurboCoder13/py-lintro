"""Shared fixtures for streaming parser tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from lintro.parsers.base_issue import BaseIssue

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class SimpleIssue(BaseIssue):
    """Simple issue for testing."""

    code: str = ""


@pytest.fixture
def parse_test_item() -> Callable[[dict[str, object]], SimpleIssue | None]:
    """Provide a parser function for test items.

    Returns:
        A function that parses dictionaries into SimpleIssue objects.
    """

    def _parse(item: dict[str, object]) -> SimpleIssue | None:
        file_val = item.get("file")
        msg_val = item.get("message")
        code_val = item.get("code")
        return SimpleIssue(
            file=str(file_val) if file_val else "",
            message=str(msg_val) if msg_val else "",
            code=str(code_val) if code_val else "",
        )

    return _parse


@pytest.fixture
def parse_error_line() -> Callable[[str], SimpleIssue | None]:
    """Provide a parser function for error lines.

    Returns:
        A function that parses lines starting with ERROR: into SimpleIssue objects.
    """

    def _parse(line: str) -> SimpleIssue | None:
        if line.startswith("ERROR:"):
            return SimpleIssue(message=line[6:].strip())
        return None

    return _parse


@pytest.fixture
def identity_line_parser() -> Callable[[str], SimpleIssue]:
    """Provide a parser that converts any line to an issue.

    Returns:
        A function that wraps any line in a SimpleIssue.
    """

    def _parse(line: str) -> SimpleIssue:
        return SimpleIssue(message=line)

    return _parse
