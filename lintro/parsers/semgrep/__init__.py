"""Semgrep parser module."""

from lintro.parsers.semgrep.semgrep_issue import SemgrepIssue
from lintro.parsers.semgrep.semgrep_parser import parse_semgrep_output

__all__ = ["SemgrepIssue", "parse_semgrep_output"]
