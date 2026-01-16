"""Shellcheck parser module.

This module provides parsing functionality for ShellCheck output, a static
analysis tool for shell scripts.
"""

from lintro.parsers.shellcheck.shellcheck_issue import ShellcheckIssue
from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output

__all__ = ["ShellcheckIssue", "parse_shellcheck_output"]
