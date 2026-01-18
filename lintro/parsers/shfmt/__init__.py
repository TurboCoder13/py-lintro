"""Shfmt parser module.

This module provides parsing utilities for shfmt output, which is a shell
script formatter supporting POSIX, Bash, and mksh shells.
"""

from lintro.parsers.shfmt.shfmt_issue import ShfmtIssue
from lintro.parsers.shfmt.shfmt_parser import parse_shfmt_output

__all__ = ["ShfmtIssue", "parse_shfmt_output"]
