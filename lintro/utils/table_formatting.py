"""Table formatting utilities for Lintro.

Functions for formatting issues as tables and getting table columns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from tabulate import tabulate

    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

from lintro.formatters import (
    ActionlintTableDescriptor,
    BanditTableDescriptor,
    BiomeTableDescriptor,
    BlackTableDescriptor,
    ClippyTableDescriptor,
    DarglintTableDescriptor,
    HadolintTableDescriptor,
    MarkdownlintTableDescriptor,
    MypyTableDescriptor,
    PrettierTableDescriptor,
    PytestFailuresTableDescriptor,
    RuffTableDescriptor,
    YamllintTableDescriptor,
    format_actionlint_issues,
    format_bandit_issues,
    format_biome_issues,
    format_black_issues,
    format_clippy_issues,
    format_darglint_issues,
    format_hadolint_issues,
    format_markdownlint_issues,
    format_mypy_issues,
    format_prettier_issues,
    format_pytest_issues,
    format_ruff_issues,
    format_yamllint_issues,
)

if TYPE_CHECKING:
    from lintro.formatters import TableDescriptor


# Constants
TOOL_TABLE_FORMATTERS: dict[str, tuple[TableDescriptor, callable]] = {
    "actionlint": (ActionlintTableDescriptor(), format_actionlint_issues),
    "bandit": (BanditTableDescriptor(), format_bandit_issues),
    "biome": (BiomeTableDescriptor(), format_biome_issues),
    "black": (BlackTableDescriptor(), format_black_issues),
    "clippy": (ClippyTableDescriptor(), format_clippy_issues),
    "darglint": (DarglintTableDescriptor(), format_darglint_issues),
    "hadolint": (HadolintTableDescriptor(), format_hadolint_issues),
    "markdownlint": (MarkdownlintTableDescriptor(), format_markdownlint_issues),
    "mypy": (MypyTableDescriptor(), format_mypy_issues),
    "prettier": (PrettierTableDescriptor(), format_prettier_issues),
    "pytest": (PytestFailuresTableDescriptor(), format_pytest_issues),
    "ruff": (RuffTableDescriptor(), format_ruff_issues),
    "yamllint": (YamllintTableDescriptor(), format_yamllint_issues),
}


def get_table_columns(
    issues: list[dict[str, str]],
    tool_name: str,
    group_by: str | None = None,
) -> tuple[list[str], list[list[str]]]:
    """Get table columns and rows for a list of issues.

    Args:
        issues: list[dict[str, str]]: List of issue dictionaries.
        tool_name: str: Name of the tool that generated the issues.
        group_by: str | None: How to group the issues (file, code, none, auto).

    Returns:
        tuple: (columns, rows) where columns is a list of column names and rows
            is a list of row data.
    """
    if not issues:
        return [], []

    # Canonical key-to-column mapping used when descriptor columns are known
    key_mapping = {
        "file": "File",
        "line": "Line",
        "column": "Column",
        "code": "Code",
        "message": "Message",
        "fixable": "Fixable",
    }

    # Get the appropriate formatter for this tool
    if tool_name in TOOL_TABLE_FORMATTERS:
        descriptor, _ = TOOL_TABLE_FORMATTERS[tool_name]
        expected_columns: list[str] = descriptor.get_columns()
        # Use expected columns but map available keys
        columns = expected_columns
    else:
        # Fallback: use all unique keys from the first issue
        columns = list(issues[0].keys()) if issues else []

    # Convert issues to rows
    rows: list[list[str]] = []
    for issue in issues:
        row: list[str] = []
        for col in columns:
            # Try to find the corresponding key in the issue dictionary
            value = ""
            for key, mapped_col in key_mapping.items():
                if mapped_col == col and key in issue:
                    value = str(issue[key])
                    break
            if not value:  # If no mapping found, try direct key match
                value = str(issue.get(col, ""))
            row.append(value)
        rows.append(row)

    return columns, rows


def format_as_table(
    issues: list[dict[str, str]],
    tool_name: str,
    group_by: str | None = None,
) -> str:
    """Format issues as a table using the appropriate formatter.

    Args:
        issues: list[dict[str, str]]: List of issue dictionaries.
        tool_name: str: Name of the tool that generated the issues.
        group_by: str | None: How to group the issues (file, code, none, auto).

    Returns:
        str: Formatted table as a string.
    """
    if not issues:
        return "No issues found."

    # Get the appropriate formatter for this tool
    if tool_name in TOOL_TABLE_FORMATTERS:
        try:
            _, formatter_func = TOOL_TABLE_FORMATTERS[tool_name]
            # Try to use the formatter, but it might expect specific issue objects
            result = formatter_func(issues=issues, format="grid")
            if result:  # If formatter worked, return the result
                return result
        except (TypeError, AttributeError):
            # Formatter failed, fall back to tabulate
            pass

    # Fallback: use tabulate if available
    if TABULATE_AVAILABLE:
        columns, rows = get_table_columns(
            issues=issues,
            tool_name=tool_name,
            group_by=group_by,
        )
        return tabulate(tabular_data=rows, headers=columns, tablefmt="grid")
    else:
        # Simple text format
        columns, rows = get_table_columns(
            issues=issues,
            tool_name=tool_name,
            group_by=group_by,
        )
        if not columns:
            return "No issues found."
        header: str = " | ".join(columns)
        separator: str = "-" * len(header)
        lines: list[str] = [header, separator]
        for row in rows:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)
