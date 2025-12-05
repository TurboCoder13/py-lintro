"""Tool utilities for handling core operations."""

import fnmatch
import os
from collections.abc import Callable

try:
    from tabulate import tabulate

    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

from lintro.formatters.tools.actionlint_formatter import (
    ActionlintTableDescriptor,
    format_actionlint_issues,
)
from lintro.formatters.tools.bandit_formatter import (
    BanditTableDescriptor,
    format_bandit_issues,
)
from lintro.formatters.tools.black_formatter import (
    BlackTableDescriptor,
    format_black_issues,
)
from lintro.formatters.tools.darglint_formatter import (
    DarglintTableDescriptor,
    format_darglint_issues,
)
from lintro.formatters.tools.hadolint_formatter import (
    HadolintTableDescriptor,
    format_hadolint_issues,
)
from lintro.formatters.tools.markdownlint_formatter import (
    MarkdownlintTableDescriptor,
    format_markdownlint_issues,
)
from lintro.formatters.tools.prettier_formatter import (
    PrettierTableDescriptor,
    format_prettier_issues,
)
from lintro.formatters.tools.pytest_formatter import (
    PytestFailuresTableDescriptor,
    format_pytest_issues,
)
from lintro.formatters.tools.ruff_formatter import (
    RuffTableDescriptor,
    format_ruff_issues,
)
from lintro.formatters.tools.yamllint_formatter import (
    YamllintTableDescriptor,
    format_yamllint_issues,
)
from lintro.parsers.bandit.bandit_parser import parse_bandit_output
from lintro.parsers.black.black_issue import BlackIssue
from lintro.parsers.black.black_parser import parse_black_output
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
from lintro.parsers.markdownlint.markdownlint_parser import parse_markdownlint_output
from lintro.parsers.prettier.prettier_issue import PrettierIssue
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.parsers.pytest.pytest_parser import parse_pytest_text_output
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.parsers.ruff.ruff_parser import parse_ruff_output
from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output

# Constants
TOOL_TABLE_FORMATTERS: dict[str, tuple] = {
    "darglint": (DarglintTableDescriptor(), format_darglint_issues),
    "hadolint": (HadolintTableDescriptor(), format_hadolint_issues),
    "black": (BlackTableDescriptor(), format_black_issues),
    "prettier": (PrettierTableDescriptor(), format_prettier_issues),
    "pytest": (PytestFailuresTableDescriptor(), format_pytest_issues),
    "ruff": (RuffTableDescriptor(), format_ruff_issues),
    "yamllint": (YamllintTableDescriptor(), format_yamllint_issues),
    "actionlint": (ActionlintTableDescriptor(), format_actionlint_issues),
    "bandit": (BanditTableDescriptor(), format_bandit_issues),
    "markdownlint": (MarkdownlintTableDescriptor(), format_markdownlint_issues),
}
VENV_PATTERNS: list[str] = [
    "venv",
    "env",
    "ENV",
    ".venv",
    ".env",
    "virtualenv",
    "virtual_env",
    "virtualenvs",
    "site-packages",
    "node_modules",
]


def parse_tool_list(tools_str: str | None) -> list[str]:
    """Parse a comma-separated list of core names into ToolEnum members.

    Args:
        tools_str: str | None: Comma-separated string of tool names, or None.

    Returns:
        list: List of ToolEnum members parsed from the input string.

    Raises:
        ValueError: If an invalid tool name is provided.
    """
    if not tools_str:
        return []
    # Import ToolEnum here to avoid circular import at module level
    from lintro.tools.tool_enum import ToolEnum

    result: list = []
    for t in tools_str.split(","):
        t = t.strip()
        if not t:
            continue
        try:
            result.append(ToolEnum[t.upper()])
        except KeyError:
            raise ValueError(f"Unknown core: {t}") from None
    return result


def parse_tool_options(tool_options_str: str | None) -> dict:
    """Parse tool-specific options.

    Args:
        tool_options_str: str | None: Comma-separated string of tool-specific
            options, or None.

    Returns:
        dict: Dictionary of parsed tool options.
    """
    if not tool_options_str:
        return {}

    options: dict = {}
    for opt in tool_options_str.split(","):
        if ":" in opt:
            tool_name, tool_opt = opt.split(":", 1)
            if "=" in tool_opt:
                opt_name, opt_value = tool_opt.split("=", 1)
                if tool_name not in options:
                    options[tool_name] = {}
                options[tool_name][opt_name] = opt_value
    return options


def should_exclude_path(
    path: str,
    exclude_patterns: list[str],
) -> bool:
    """Check if a path should be excluded based on patterns.

    Args:
        path: str: File path to check for exclusion.
        exclude_patterns: list[str]: List of glob patterns to match against.

    Returns:
        bool: True if the path should be excluded, False otherwise.
    """
    if not exclude_patterns:
        return False

    # Normalize path separators for cross-platform compatibility
    normalized_path: str = path.replace("\\", "/")

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(normalized_path, pattern):
            return True
        # Also check if the pattern matches any part of the path
        path_parts: list[str] = normalized_path.split("/")
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


def get_table_columns(
    issues: list[dict[str, str]],
    tool_name: str,
    group_by: str | None = None,
) -> tuple[list[str], list[str]]:
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


def format_tool_output(
    tool_name: str,
    output: str,
    group_by: str = "auto",
    output_format: str = "grid",
    issues: list[object] | None = None,
) -> str:
    """Format tool output using the specified format.

    Args:
        tool_name: str: Name of the tool that generated the output.
        output: str: Raw output from the tool.
        group_by: str: How to group issues (file, code, none, auto).
        output_format: str: Output format (plain, grid, markdown, html, json, csv).
        issues: list[object] | None: List of parsed issue objects (optional).

    Returns:
        str: Formatted output string.
    """
    # If parsed issues are provided, prefer them regardless of raw output
    if issues and tool_name in TOOL_TABLE_FORMATTERS:
        # Fixability predicates per tool
        def _is_fixable_predicate(tool: str) -> Callable[[object], bool] | None:
            if tool == "ruff":
                return lambda i: isinstance(i, RuffFormatIssue) or (
                    isinstance(i, RuffIssue) and getattr(i, "fixable", False)
                )
            if tool == "prettier":
                return lambda i: isinstance(i, PrettierIssue)
            if tool == "black":
                return lambda i: isinstance(i, BlackIssue) and getattr(
                    i,
                    "fixable",
                    True,
                )
            return None

        is_fixable = _is_fixable_predicate(tool_name)

        if output_format != "json" and is_fixable is not None and TABULATE_AVAILABLE:
            descriptor, _ = TOOL_TABLE_FORMATTERS[tool_name]

            fixable_issues = [i for i in issues if is_fixable(i)]
            non_fixable_issues = [i for i in issues if not is_fixable(i)]

            sections: list[str] = []
            if fixable_issues:
                cols_f = descriptor.get_columns()
                rows_f = descriptor.get_rows(fixable_issues)
                table_f = tabulate(
                    tabular_data=rows_f,
                    headers=cols_f,
                    tablefmt="grid",
                    stralign="left",
                    disable_numparse=True,
                )
                sections.append("Auto-fixable issues\n" + table_f)
            if non_fixable_issues:
                cols_u = descriptor.get_columns()
                rows_u = descriptor.get_rows(non_fixable_issues)
                table_u = tabulate(
                    tabular_data=rows_u,
                    headers=cols_u,
                    tablefmt="grid",
                    stralign="left",
                    disable_numparse=True,
                )
                sections.append("Not auto-fixable issues\n" + table_u)
            if sections:
                return "\n\n".join(sections)

        # Fallback to tool-specific formatter on provided issues
        _, formatter_func = TOOL_TABLE_FORMATTERS[tool_name]
        return formatter_func(issues=issues, format=output_format)

    if not output or not output.strip():
        return "No issues found."

    # If we have parsed issues, prefer centralized split-by-fixability when
    # a predicate is known for this tool (non-JSON formats only). Otherwise
    # fall back to the tool-specific formatter.

    # Otherwise, try to parse the output and format it
    parsed_issues: list = []
    if tool_name == "ruff":
        parsed_issues = parse_ruff_output(output=output)
    elif tool_name == "prettier":
        parsed_issues = parse_prettier_output(output=output)
    elif tool_name == "black":
        parsed_issues = parse_black_output(output=output)
    elif tool_name == "darglint":
        parsed_issues = parse_darglint_output(output=output)
    elif tool_name == "hadolint":
        parsed_issues = parse_hadolint_output(output=output)
    elif tool_name == "yamllint":
        parsed_issues = parse_yamllint_output(output=output)
    elif tool_name == "markdownlint":
        parsed_issues = parse_markdownlint_output(output=output)
    elif tool_name == "bandit":
        # Bandit emits JSON; try parsing when raw output is provided
        try:
            parsed_issues = parse_bandit_output(
                bandit_data=__import__("json").loads(output),
            )
        except Exception:
            parsed_issues = []
    elif tool_name == "pytest":
        # Pytest emits text output; parse it
        parsed_issues = parse_pytest_text_output(output=output)

    if parsed_issues and tool_name in TOOL_TABLE_FORMATTERS:
        _, formatter_func = TOOL_TABLE_FORMATTERS[tool_name]
        return formatter_func(issues=parsed_issues, format=output_format)

    # Fallback: return the raw output
    return output


def walk_files_with_excludes(
    paths: list[str],
    file_patterns: list[str],
    exclude_patterns: list[str],
    include_venv: bool = False,
) -> list[str]:
    """Return files under ``paths`` matching patterns and not excluded.

    Args:
        paths: list[str]: Files or directories to search.
        file_patterns: list[str]: Glob patterns to include.
        exclude_patterns: list[str]: Glob patterns to exclude.
        include_venv: bool: Include virtual environment directories when True.

    Returns:
        list[str]: Sorted file paths matching include filters and not excluded.
    """
    all_files: list[str] = []

    for path in paths:
        if os.path.isfile(path):
            # Single file - check if the filename matches any file pattern
            filename = os.path.basename(path)
            for pattern in file_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    all_files.append(path)
                    break
        elif os.path.isdir(path):
            # Directory - walk through it
            for root, dirs, files in os.walk(path):
                # Filter out virtual environment directories unless include_venv is True
                if not include_venv:
                    dirs[:] = [d for d in dirs if not _is_venv_directory(d)]

                # Check each file against the patterns
                for file in files:
                    file_path: str = os.path.join(root, file)
                    rel_path: str = os.path.relpath(file_path, path)

                    # Check if file matches any file pattern
                    matches_pattern: bool = False
                    for pattern in file_patterns:
                        if fnmatch.fnmatch(file, pattern):
                            matches_pattern = True
                            break

                    if matches_pattern and not should_exclude_path(
                        path=rel_path,
                        exclude_patterns=exclude_patterns,
                    ):
                        all_files.append(file_path)

    return sorted(all_files)


def _is_venv_directory(dirname: str) -> bool:
    """Check if a directory name indicates a virtual environment.

    Args:
        dirname: str: Directory name to check.

    Returns:
        bool: True if the directory appears to be a virtual environment.
    """
    return dirname in VENV_PATTERNS
