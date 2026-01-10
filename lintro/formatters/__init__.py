"""Formatters for converting tool outputs into human-friendly tables.

This module provides the unified formatting approach that works with any
tool's issues by using the BaseIssue.to_display_row() method.
"""

# Base classes and utilities
from lintro.formatters.core.format_registry import OutputStyle, TableDescriptor

# Unified formatter - the preferred way to format issues
from lintro.formatters.formatter import (
    EXTENDED_COLUMNS,
    STANDARD_COLUMNS,
    UnifiedTableDescriptor,
    format_issues,
    format_issues_with_sections,
    format_tool_result,
)

__all__ = [
    # Unified formatter (primary API)
    "format_issues",
    "format_issues_with_sections",
    "format_tool_result",
    "UnifiedTableDescriptor",
    "STANDARD_COLUMNS",
    "EXTENDED_COLUMNS",
    # Base classes
    "TableDescriptor",
    "OutputStyle",
]
