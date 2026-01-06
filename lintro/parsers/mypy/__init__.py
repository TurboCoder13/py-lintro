"""Mypy parser package."""

from lintro.parsers.mypy.mypy_issue import MypyIssue
from lintro.parsers.mypy.mypy_parser import parse_mypy_output

__all__ = ["MypyIssue", "parse_mypy_output"]
