"""Output formatting utilities for Lintro.

Functions for formatting tool output with various formatters and parsers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger

from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.enums.tool_name import ToolName

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
from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output
from lintro.parsers.bandit.bandit_parser import parse_bandit_output
from lintro.parsers.biome.biome_issue import BiomeIssue
from lintro.parsers.biome.biome_parser import parse_biome_output
from lintro.parsers.black.black_issue import BlackIssue
from lintro.parsers.black.black_parser import parse_black_output
from lintro.parsers.clippy.clippy_parser import parse_clippy_output
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
from lintro.parsers.markdownlint.markdownlint_parser import parse_markdownlint_output
from lintro.parsers.mypy.mypy_parser import parse_mypy_output
from lintro.parsers.prettier.prettier_issue import PrettierIssue
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.parsers.pytest.pytest_parser import parse_pytest_text_output
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue

if TYPE_CHECKING:
    from lintro.formatters import TableDescriptor

# Constants
TOOL_TABLE_FORMATTERS: dict[str, tuple[TableDescriptor, Callable[..., str]]] = {
    ToolName.ACTIONLINT: (ActionlintTableDescriptor(), format_actionlint_issues),
    ToolName.BANDIT: (BanditTableDescriptor(), format_bandit_issues),
    ToolName.BIOME: (BiomeTableDescriptor(), format_biome_issues),
    ToolName.BLACK: (BlackTableDescriptor(), format_black_issues),
    ToolName.CLIPPY: (ClippyTableDescriptor(), format_clippy_issues),
    ToolName.DARGLINT: (DarglintTableDescriptor(), format_darglint_issues),
    ToolName.HADOLINT: (HadolintTableDescriptor(), format_hadolint_issues),
    ToolName.MARKDOWNLINT: (MarkdownlintTableDescriptor(), format_markdownlint_issues),
    ToolName.MYPY: (MypyTableDescriptor(), format_mypy_issues),
    ToolName.PRETTIER: (PrettierTableDescriptor(), format_prettier_issues),
    ToolName.PYTEST: (PytestFailuresTableDescriptor(), format_pytest_issues),
    ToolName.RUFF: (RuffTableDescriptor(), format_ruff_issues),
    ToolName.YAMLLINT: (YamllintTableDescriptor(), format_yamllint_issues),
}


def format_tool_output(
    tool_name: str,
    output: str,
    output_format: str | OutputFormat = "grid",
    issues: list[object] | None = None,
) -> str:
    """Format tool output using the specified format.

    Args:
        tool_name: str: Name of the tool that generated the output.
        output: str: Raw output from the tool.
        output_format: str: Output format (plain, grid, markdown, html, json, csv).
        issues: list[object] | None: List of parsed issue objects (optional).

    Returns:
        str: Formatted output string.
    """
    output_format = normalize_output_format(output_format)

    # If parsed issues are provided, prefer them regardless of raw output
    if issues and tool_name in TOOL_TABLE_FORMATTERS:
        # Fixability predicates per tool
        def _is_fixable_predicate(tool: str) -> Callable[[object], bool] | None:
            if tool == ToolName.RUFF:
                return lambda i: isinstance(i, RuffFormatIssue) or (
                    isinstance(i, RuffIssue) and getattr(i, "fixable", False)
                )
            if tool == ToolName.PRETTIER:
                return lambda i: isinstance(i, PrettierIssue)
            if tool == ToolName.BLACK:
                return lambda i: isinstance(i, BlackIssue) and getattr(
                    i,
                    "fixable",
                    True,
                )
            if tool == ToolName.BIOME:
                return lambda i: isinstance(i, BiomeIssue) and getattr(
                    i,
                    "fixable",
                    False,
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
                    tablefmt=output_format,
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
                    tablefmt=output_format,
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

    # Try to parse the output and format it using tool-specific parsers
    parsed_issues: list[Any] = []
    if tool_name == ToolName.RUFF:
        from lintro.parsers.ruff.ruff_parser import parse_ruff_output

        parsed_issues = list(parse_ruff_output(output=output))
    elif tool_name == ToolName.PRETTIER:
        parsed_issues = list(parse_prettier_output(output=output))
    elif tool_name == ToolName.ACTIONLINT:
        parsed_issues = list(parse_actionlint_output(output=output))
    elif tool_name == ToolName.BIOME:
        parsed_issues = list(parse_biome_output(output=output))
    elif tool_name == ToolName.MYPY:
        parsed_issues = list(parse_mypy_output(output=output))
    elif tool_name == ToolName.BLACK:
        parsed_issues = list(parse_black_output(output=output))
    elif tool_name == ToolName.DARGLINT:
        parsed_issues = list(parse_darglint_output(output=output))
    elif tool_name == ToolName.HADOLINT:
        parsed_issues = list(parse_hadolint_output(output=output))
    elif tool_name == ToolName.YAMLLINT:
        from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output

        parsed_issues = list(parse_yamllint_output(output=output))
    elif tool_name == ToolName.MARKDOWNLINT:
        parsed_issues = list(parse_markdownlint_output(output=output))
    elif tool_name == ToolName.BANDIT:
        # Bandit emits JSON; try parsing when raw output is provided
        try:
            parsed_issues = parse_bandit_output(
                bandit_data=json.loads(output),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse Bandit output: {e}")
            parsed_issues = []
    elif tool_name == ToolName.CLIPPY:
        parsed_issues = list(parse_clippy_output(output=output))
    elif tool_name == ToolName.PYTEST:
        # Pytest emits text output; parse it
        parsed_issues = list(parse_pytest_text_output(output=output))

    if parsed_issues and tool_name in TOOL_TABLE_FORMATTERS:
        _, formatter_func = TOOL_TABLE_FORMATTERS[tool_name]
        return formatter_func(issues=parsed_issues, format=output_format)

    # Fallback: return the raw output
    return output
