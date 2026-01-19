"""SQLFluff parser module."""

from lintro.parsers.sqlfluff.sqlfluff_issue import SqlfluffIssue
from lintro.parsers.sqlfluff.sqlfluff_parser import parse_sqlfluff_output

__all__ = ["SqlfluffIssue", "parse_sqlfluff_output"]
