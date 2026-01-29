"""Tsc (TypeScript Compiler) parser package."""

from lintro.parsers.tsc.tsc_issue import TscIssue
from lintro.parsers.tsc.tsc_parser import parse_tsc_output

__all__ = ["TscIssue", "parse_tsc_output"]
