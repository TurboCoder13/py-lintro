"""Gitleaks parser module."""

from lintro.parsers.gitleaks.gitleaks_issue import GitleaksIssue
from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output

__all__ = ["GitleaksIssue", "parse_gitleaks_output"]
