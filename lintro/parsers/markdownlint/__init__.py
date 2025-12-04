"""Parser for markdownlint-cli2 output."""

from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue
from lintro.parsers.markdownlint.markdownlint_parser import parse_markdownlint_output

__all__ = ["MarkdownlintIssue", "parse_markdownlint_output"]
