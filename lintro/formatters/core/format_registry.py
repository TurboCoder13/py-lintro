"""Core formatting abstractions and style registry.

This module provides:
- OutputStyle: Abstract base class for output style renderers
- TableDescriptor: Interface for describing table columns and rows
- Style registry functions for looking up format styles
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from lintro.enums.output_format import OutputFormat

if TYPE_CHECKING:
    pass


# =============================================================================
# Abstract Base Classes
# =============================================================================


class OutputStyle(ABC):
    """Abstract base class for output style renderers.

    Implementations convert tabular data into a concrete textual
    representation (e.g., grid, markdown, plain).
    """

    @abstractmethod
    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a table given columns and rows.

        Args:
            columns: List of column header names.
            rows: List of rows, where each row is a list of values.
            tool_name: Optional tool name for metadata-rich formats.
            **kwargs: Additional renderer-specific context.

        Returns:
            str: Formatted table as a string.
        """
        pass


class TableDescriptor(ABC):
    """Describe how to extract tabular data for a tool's issues.

    Concrete implementations define column ordering and how to map issue
    objects into a list of column values.
    """

    @abstractmethod
    def get_columns(self) -> list[str]:
        """Return the list of column names in order."""
        pass

    @abstractmethod
    def get_rows(
        self,
        issues: list[Any],
    ) -> list[list[Any]]:
        """Return the values for each column for a list of issues.

        Args:
            issues: List of issue objects to extract data from.

        Returns:
            list[list]: Nested list representing table rows and columns.
        """
        pass


# =============================================================================
# Style Registry
# =============================================================================


@lru_cache(maxsize=1)
def _create_style_instances() -> dict[OutputFormat, OutputStyle]:
    """Create singleton instances of all output styles.

    Uses lazy imports to avoid circular dependencies and improve startup time.
    Results are cached to ensure style instances are reused.

    Returns:
        dict[OutputFormat, OutputStyle]: Mapping of format to style instance.
    """
    from lintro.formatters.styles.csv import CsvStyle
    from lintro.formatters.styles.grid import GridStyle
    from lintro.formatters.styles.html import HtmlStyle
    from lintro.formatters.styles.json import JsonStyle
    from lintro.formatters.styles.markdown import MarkdownStyle
    from lintro.formatters.styles.plain import PlainStyle

    return {
        OutputFormat.PLAIN: PlainStyle(),
        OutputFormat.GRID: GridStyle(),
        OutputFormat.MARKDOWN: MarkdownStyle(),
        OutputFormat.HTML: HtmlStyle(),
        OutputFormat.JSON: JsonStyle(),
        OutputFormat.CSV: CsvStyle(),
    }


def get_style(format_key: OutputFormat | str) -> OutputStyle:
    """Get the output style for a given format.

    Args:
        format_key: Output format as enum or string (e.g., "grid", "plain").

    Returns:
        OutputStyle: The appropriate style instance for formatting.
            Falls back to GridStyle for unknown formats to maintain
            backward compatibility.
    """
    styles = _create_style_instances()

    # Handle string keys for backward compatibility
    if isinstance(format_key, str):
        format_key_lower = format_key.lower()
        try:
            format_key = OutputFormat(format_key_lower)
        except ValueError:
            # Try matching by name
            for fmt in OutputFormat:
                if (
                    fmt.value == format_key_lower
                    or fmt.name.lower() == format_key_lower
                ):
                    format_key = fmt
                    break
            else:
                # Fallback to cached GridStyle for unknown formats
                return styles[OutputFormat.GRID]

    style = styles.get(format_key)
    if style is None:
        # Fallback to cached grid style
        return styles[OutputFormat.GRID]

    return style


def get_format_map() -> dict[OutputFormat, OutputStyle]:
    """Get the complete format map for direct access.

    This provides backward compatibility for code that expects a FORMAT_MAP dict.

    Returns:
        dict[OutputFormat, OutputStyle]: Complete mapping of all formats to styles.
    """
    return _create_style_instances()


def get_string_format_map() -> dict[str, OutputStyle]:
    """Get format map with string keys for backward compatibility.

    Some formatters use string keys like "grid" instead of OutputFormat.GRID.

    Returns:
        dict[str, OutputStyle]: Mapping with string keys.
    """
    styles = _create_style_instances()
    return {fmt.value: style for fmt, style in styles.items()}


# Convenience constants for common use cases
DEFAULT_FORMAT = OutputFormat.GRID
