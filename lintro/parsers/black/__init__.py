"""Black code formatter parser."""

from .black_issue import BlackIssue
from .black_parser import parse_black_output

__all__ = ["BlackIssue", "parse_black_output"]
