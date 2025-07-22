"""Tool utilities for handling core operations."""

import os
import fnmatch
from loguru import logger

try:
    from tabulate import tabulate

    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

from lintro.formatters.tools.darglint_formatter import (
    DarglintTableDescriptor,
    format_darglint_issues,
)
from lintro.formatters.tools.prettier_formatter import (
    PrettierTableDescriptor,
    format_prettier_issues,
)
from lintro.formatters.tools.ruff_formatter import (
    RuffTableDescriptor,
    format_ruff_issues,
)
from lintro.utils.path_utils import normalize_file_path_for_display

from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.parsers.ruff.ruff_parser import parse_ruff_output


TOOL_TABLE_FORMATTERS = {
    "darglint": (DarglintTableDescriptor(), format_darglint_issues),
    "prettier": (PrettierTableDescriptor(), format_prettier_issues),
    "ruff": (RuffTableDescriptor(), format_ruff_issues),
    # Add more tools here as you implement TableDescriptor/formatter for them
}


def parse_tool_list(tools_str: str | None) -> list:
    """Parse a comma-separated list of core names into ToolEnum members.

    Args:
        tools_str: Comma-separated string of tool names, or None.

    Returns:
        list: List of ToolEnum members parsed from the input string.

    Raises:
        ValueError: If an invalid tool name is provided.
    """
    if not tools_str:
        return []
    # Import ToolEnum here to avoid circular import at module level
    from lintro.tools.tool_enum import ToolEnum

    result = []
    for t in tools_str.split(","):
        t = t.strip()
        if not t:
            continue
        try:
            result.append(ToolEnum[t.upper()])
        except KeyError:
            raise ValueError(f"Unknown core: {t}")
    return result


def parse_tool_options(tool_options_str: str | None) -> dict:
    """Parse tool-specific options.

    Args:
        tool_options_str: Comma-separated string of tool-specific options, or None.

    Returns:
        dict: Dictionary of parsed tool options.
    """
    if not tool_options_str:
        return {}

    options = {}
    for opt in tool_options_str.split(","):
        if ":" in opt:
            tool_name, tool_opt = opt.split(":", 1)
            if "=" in tool_opt:
                opt_name, opt_value = tool_opt.split("=", 1)
                if tool_name not in options:
                    options[tool_name] = {}
                options[tool_name][opt_name] = opt_value
    return options


def should_exclude_path(path: str, exclude_patterns: list[str]) -> bool:
    """Check if a path should be excluded based on patterns.

    Args:
        path: File path to check for exclusion.
        exclude_patterns: List of glob patterns to match against.

    Returns:
        bool: True if path should be excluded, False otherwise.
    """
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def get_table_columns(
    issues: list[dict[str, str]], tool_name: str, group_by: str | None = None
) -> tuple[list[str], list[str]]:
    """Get appropriate columns for displaying issues in a table.

    Args:
        issues: List of issues to analyze.
        tool_name: Name of the tool that found the issues.
        group_by: How to group the issues (file, code, or none).

    Returns:
        Tuple of (display_columns, data_columns).
    """
    if not issues:
        return [], []

    # Determine available columns from the first issue
    available_columns = list(issues[0].keys())

    # Standard column order preferences
    column_preferences = [
        "file",
        "line",
        "column",
        "code",
        "message",
        "severity",
        "rule",
    ]

    # Order columns based on preferences
    ordered_columns = []
    for pref in column_preferences:
        if pref in available_columns:
            ordered_columns.append(pref)

    # Add any remaining columns
    for col in available_columns:
        if col not in ordered_columns:
            ordered_columns.append(col)

    # Adjust based on grouping
    if group_by == "file":
        # When grouping by file, we might want to hide the file column in individual tables
        display_columns = [col.title() for col in ordered_columns]
        data_columns = ordered_columns
    elif group_by == "code":
        # When grouping by code, we might want to highlight the code column
        display_columns = [col.title() for col in ordered_columns]
        data_columns = ordered_columns
    else:
        # No special grouping adjustments
        display_columns = [col.title() for col in ordered_columns]
        data_columns = ordered_columns

    return display_columns, data_columns


def format_as_table(
    issues: list[dict[str, str]],
    tool_name: str,
    group_by: str | None = None,
) -> str:
    """Format issues as a table.

    Args:
        issues: List of issues to format.
        tool_name: Name of the core that found the issues.
        group_by: How to group the issues (file, code, or none).

    Returns:
        Formatted table as a string, or empty string if no issues.
    """
    if not issues:
        return ""  # Let the caller handle "No issues found" display

    # Get the columns for this core
    display_columns, data_columns = get_table_columns(issues, tool_name, group_by)
    rows = [[issue.get(col, "") for col in data_columns] for issue in issues]

    if TABULATE_AVAILABLE:
        table = tabulate(rows, headers=display_columns, tablefmt="grid")
    else:
        # Fallback: simple text table
        header = " | ".join(display_columns)
        sep = " | ".join(["-" * len(col) for col in display_columns])
        table_lines = [header, sep]
        for row in rows:
            table_lines.append(" | ".join(str(cell) for cell in row))
        table = "\n".join(table_lines)

    if group_by == "file":
        result = ""
        files = sorted(set(issue["file"] for issue in issues))
        for file in files:
            result += f"File: {file}\n"
        result += table
        return result
    elif group_by == "code":
        result = ""
        codes = sorted(set(issue.get("code", "") for issue in issues))
        for code in codes:
            result += f"PEP Code: {code}\n"
        result += table
        return result
    else:
        return table


def format_tool_output(
    tool_name: str,
    output: str,
    group_by: str = "auto",
    output_format: str = "grid",
) -> str:
    """Format core output based on core type and format preference.

    Uses tool-specific TableDescriptor and formatter for the tool if available.
    Falls back to generic formatting logic if not available.

    Args:
        tool_name: Name of the core that generated the output.
        output: Raw output from the core.
        group_by: How to group issues (file, code, none, auto).
        output_format: Output format for displaying results (plain, grid, markdown, html, json, csv)

    Returns:
        Formatted output string, or empty string if no issues.
    """
    if not output.strip():
        return ""  # Let the footer handle "No issues found" display

    # Use tool-specific TableDescriptor/formatter if available
    if tool_name in TOOL_TABLE_FORMATTERS:
        issues = []
        if tool_name == "darglint":
            issues = parse_darglint_output(output)
        elif tool_name == "prettier":
            issues = parse_prettier_output(output)
        elif tool_name == "ruff":
            issues = parse_ruff_output(output)
        descriptor, formatter = TOOL_TABLE_FORMATTERS[tool_name]
        return formatter(issues, format=output_format)
    else:
        # Fallback to generic formatting logic for tools without specific formatters
        try:
            # For tools that don't have specific parsers,
            # attempt to parse as generic format or return raw output
            lines = output.strip().split("\n")
            if lines and any(line.strip() for line in lines):
                # If we have meaningful output, try to parse it as generic issues
                # This is a basic fallback - for better formatting, tools should implement specific parsers
                issues = []
                for line in lines:
                    if line.strip() and not line.startswith("*"):  # Skip header lines
                        # Try basic parsing - this is very generic
                        parts = line.split(":")
                        if len(parts) >= 3:
                            file_part = parts[0].strip()
                            line_part = parts[1].strip() if len(parts) > 1 else ""
                            message_part = (
                                ":".join(parts[2:]).strip() if len(parts) > 2 else ""
                            )
                            issues.append(
                                {
                                    "file": normalize_file_path_for_display(file_part),
                                    "line": line_part,
                                    "code": "",
                                    "message": message_part,
                                }
                            )

                if issues:
                    # Use the grid formatter for generic issues
                    from lintro.formatters.styles.plain import PlainStyle
                    from lintro.formatters.styles.grid import GridStyle
                    from lintro.formatters.styles.markdown import MarkdownStyle
                    from lintro.formatters.styles.html import HtmlStyle
                    from lintro.formatters.styles.json import JsonStyle
                    from lintro.formatters.styles.csv import CsvStyle

                    format_map = {
                        "plain": PlainStyle(),
                        "grid": GridStyle(),
                        "markdown": MarkdownStyle(),
                        "html": HtmlStyle(),
                        "json": JsonStyle(),
                        "csv": CsvStyle(),
                    }

                    formatter = format_map.get(output_format, GridStyle())
                    columns = ["File", "Line", "Code", "Message"]
                    rows = [
                        [issue["file"], issue["line"], issue["code"], issue["message"]]
                        for issue in issues
                    ]
                    return formatter.format(columns, rows)
                else:
                    # If parsing failed, return raw output
                    return output
            else:
                return ""  # Let the caller handle "No issues found" display
        except Exception:
            # If any parsing fails, return raw output
            return output


def walk_files_with_excludes(
    paths: list[str],
    file_patterns: list[str],
    exclude_patterns: list[str],
    include_venv: bool = False,
) -> list[str]:
    """Recursively walk given paths, yielding files matching file_patterns and not matching exclude patterns.

    Supports .lintro-ignore at the project root or current working directory, using .gitignore-style semantics:
    - Patterns are matched against the relative path from the project root (os.getcwd()).
    - Negation patterns (starting with '!') are supported (un-ignore).
    - Recursive globs (e.g., 'foo/**') are supported.
    - Patterns are applied in order; the last match wins.

    Args:
        paths: List of file or directory paths to walk.
        file_patterns: List of glob patterns for files to include (e.g., ['*.py']).
        exclude_patterns: List of glob patterns or directory names to exclude.
        include_venv: Whether to include virtual environment and dependency directories.

    Returns:
        List of file paths matching the criteria.
    """
    logger.debug(
        f"walk_files_with_excludes paths: {paths} types: {[type(p) for p in paths]}"
    )
    logger.debug(f"os.getcwd(): {os.getcwd()}")
    logger.debug(f"file_patterns: {file_patterns}")
    result = []
    exclude_dirs = set(
        [
            ".venv",
            "venv",
            "env",
            "ENV",
            "site-packages",
            "node_modules",
            "__pycache__",
            ".tox",
            ".pytest_cache",
            "dist",
            "build",
        ]
    )
    # Try to read .lintro-ignore from project root or cwd
    ignore_file = None
    for candidate in [
        os.path.join(os.getcwd(), ".lintro-ignore"),
        os.path.join(os.path.dirname(os.path.abspath(paths[0])), ".lintro-ignore"),
    ]:
        if os.path.isfile(candidate):
            ignore_file = candidate
            break
    ignore_patterns = []
    if ignore_file:
        with open(ignore_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                ignore_patterns.append(line)
    # Merge CLI and file patterns, preserving order
    all_patterns = list(exclude_patterns) + ignore_patterns
    logger.debug(f"all_patterns (exclude + ignore): {all_patterns}")
    project_root = os.getcwd()

    def is_excluded(rel_path: str) -> bool:
        """Apply .gitignore-style pattern logic to rel_path.

        Args:
            rel_path: Relative path to check against patterns.

        Returns:
            bool: True if path is excluded, False otherwise.
        """
        excluded = False
        for pat in all_patterns:
            neg = pat.startswith("!")
            pat_clean = pat[1:] if neg else pat
            if fnmatch.fnmatchcase(rel_path, pat_clean):
                excluded = not neg
        return excluded

    for path in paths:
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, project_root)
            basename = os.path.basename(rel_path)
            pattern_match = [
                (
                    pat,
                    fnmatch.fnmatchcase(rel_path, pat),
                    fnmatch.fnmatchcase(basename, pat),
                )
                for pat in file_patterns
            ]
            logger.debug(
                f"Checking file: {path}, rel_path: {rel_path}, basename: {basename}, pattern_match: {pattern_match}"
            )
            excluded = is_excluded(rel_path)
            logger.debug(f"is_excluded({rel_path}) = {excluded}")
            if any(r or b for _, r, b in pattern_match):
                if not excluded:
                    result.append(path)
            continue
        for root, dirs, files in os.walk(path):
            rel_dir = os.path.relpath(root, project_root)
            # Exclude dirs using .gitignore-style logic
            dirs[:] = [
                d
                for d in dirs
                if (
                    (include_venv or d not in exclude_dirs)
                    and not is_excluded(os.path.normpath(os.path.join(rel_dir, d)))
                )
            ]
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                basename = os.path.basename(rel_path)
                pattern_match = [
                    (
                        pat,
                        fnmatch.fnmatchcase(rel_path, pat),
                        fnmatch.fnmatchcase(basename, pat),
                    )
                    for pat in file_patterns
                ]
                logger.debug(
                    f"Checking file: {file_path}, rel_path: {rel_path}, basename: {basename}, pattern_match: {pattern_match}"
                )
                excluded = is_excluded(rel_path)
                logger.debug(f"is_excluded({rel_path}) = {excluded}")
                if any(r or b for _, r, b in pattern_match):
                    if not excluded:
                        result.append(file_path)
    return result
