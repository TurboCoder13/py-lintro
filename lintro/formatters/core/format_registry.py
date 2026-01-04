"""Centralized format style registry for all formatters.

This module provides a shared registry of output format styles, eliminating
the duplicate FORMAT_MAP definitions across individual formatter modules.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from lintro.enums.output_format import OutputFormat

if TYPE_CHECKING:
    from lintro.formatters.core.output_style import OutputStyle


@lru_cache(maxsize=1)
def _create_style_instances() -> dict[OutputFormat, "OutputStyle"]:
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


def get_style(format_key: OutputFormat | str) -> "OutputStyle":
    """Get the output style for a given format.

    Args:
        format_key: Output format as enum or string (e.g., "grid", "plain").

    Returns:
        OutputStyle: The appropriate style instance for formatting.

    Raises:
        ValueError: If format_key is not a valid format.
    """
    styles = _create_style_instances()

    # Handle string keys for backward compatibility
    if isinstance(format_key, str):
        format_key = format_key.lower()
        try:
            format_key = OutputFormat(format_key)
        except ValueError:
            # Try matching by name
            for fmt in OutputFormat:
                if fmt.value == format_key or fmt.name.lower() == format_key:
                    format_key = fmt
                    break
            else:
                raise ValueError(
                    f"Unknown format: {format_key}. "
                    f"Valid formats: {[f.value for f in OutputFormat]}"
                )

    style = styles.get(format_key)
    if style is None:
        # Fallback to grid style
        from lintro.formatters.styles.grid import GridStyle

        return GridStyle()

    return style


def get_format_map() -> dict[OutputFormat, "OutputStyle"]:
    """Get the complete format map for direct access.

    This provides backward compatibility for code that expects a FORMAT_MAP dict.

    Returns:
        dict[OutputFormat, OutputStyle]: Complete mapping of all formats to styles.
    """
    return _create_style_instances()


def get_string_format_map() -> dict[str, "OutputStyle"]:
    """Get format map with string keys for backward compatibility.

    Some formatters use string keys like "grid" instead of OutputFormat.GRID.

    Returns:
        dict[str, OutputStyle]: Mapping with string keys.
    """
    styles = _create_style_instances()
    return {fmt.value: style for fmt, style in styles.items()}


# Convenience constants for common use cases
DEFAULT_FORMAT = OutputFormat.GRID
