"""Pydoclint parser module.

This module provides parsing functionality for pydoclint output, a Python
docstring linter that validates docstrings match function signatures.
"""

from lintro.parsers.pydoclint.pydoclint_issue import PydoclintIssue
from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output

__all__ = ["PydoclintIssue", "parse_pydoclint_output"]
