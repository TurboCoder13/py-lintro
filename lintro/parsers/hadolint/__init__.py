"""Hadolint parser module."""

from lintro.parsers.hadolint.hadolint_issue import HadolintIssue
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output

__all__ = ["HadolintIssue", "parse_hadolint_output"]
