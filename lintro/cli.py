"""Command-line interface for Lintro."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import click

from lintro import __version__
from lintro.tools import AVAILABLE_TOOLS, CHECK_TOOLS, FIX_TOOLS


@dataclass
class ToolResult:
    """Result of running a tool."""
    name: str
    success: bool
    output: str
    issues_count: int = 0


def count_issues(output: str, tool_name: str) -> int:
    """Count the number of issues in the tool output."""
    if tool_name == "black":
        # Count "would reformat" lines
        return len(re.findall(r"would reformat", output))
    elif tool_name == "isort":
        # Count "ERROR:" lines for isort
        return len(re.findall(r"ERROR:", output))
    elif tool_name == "flake8":
        # Count lines with error codes (e.g., E501, W291)
        return len(re.findall(r":\d+:\d+: [EWFN]\d{3} ", output))
    else:
        # Generic fallback: count lines that look like issues
        return len(re.findall(r"(error|warning|issue|problem)", output, re.IGNORECASE))


def print_tool_header(tool_name: str, action: str):
    """Print a header for a tool's output."""
    click.secho(f"\n{'=' * 60}", fg="blue")
    click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True)
    click.secho(f"{'=' * 60}", fg="blue")


def print_tool_footer(success: bool, issues_count: int):
    """Print a footer for a tool's output."""
    if success:
        click.secho(f"\n✓ No issues found", fg="green")
    else:
        click.secho(f"\n✗ Found {issues_count} issues", fg="red")
    click.secho(f"{'-' * 60}", fg="blue")


def print_summary(results: List[ToolResult], action: str):
    """Print a summary of all tool results."""
    total_issues = sum(result.issues_count for result in results)
    
    click.secho(f"\n{'=' * 60}", fg="yellow")
    click.secho(f" Summary ({action})", fg="yellow", bold=True)
    click.secho(f"{'=' * 60}", fg="yellow")
    
    for result in results:
        status = "✓" if result.success else "✗"
        color = "green" if result.success else "red"
        issues_text = "No issues" if result.issues_count == 0 else f"{result.issues_count} issues"
        click.secho(f" {status} {result.name}: {issues_text}", fg=color)
    
    click.secho(f"{'-' * 60}", fg="yellow")
    
    if total_issues == 0:
        click.secho(f" Total: No issues found", fg="green")
    else:
        click.secho(f" Total: {total_issues} issues found", fg="red")
    
    click.secho(f"{'=' * 60}", fg="yellow")


def parse_tool_list(tools_str: Optional[str]) -> List[str]:
    """Parse a comma-separated list of tool names."""
    if not tools_str:
        return []
    return [t.strip() for t in tools_str.split(",") if t.strip()]


def format_tool_output(output: str, tool_name: str) -> str:
    """Format the output of a tool to be more readable."""
    if not output:
        return "No output"
    
    # Remove trailing whitespace and ensure ending with newline
    output = output.rstrip() + "\n"
    
    if tool_name == "black":
        # Colorize Black output
        output = re.sub(r"(would reformat .*)", click.style(r"\1", fg="yellow"), output)
        output = re.sub(r"(All done!.*)", click.style(r"\1", fg="green"), output)
        output = re.sub(r"(Oh no!.*)", click.style(r"\1", fg="red"), output)
    elif tool_name == "isort":
        # Colorize isort output
        output = re.sub(r"(ERROR:.*)", click.style(r"\1", fg="red"), output)
        output = re.sub(r"(Skipped \d+ files)", click.style(r"\1", fg="yellow"), output)
    elif tool_name == "flake8":
        # Colorize flake8 output (line:col: code message)
        output = re.sub(
            r"(.*:\d+:\d+: [EWFN]\d{3} .*)",
            click.style(r"\1", fg="red"),
            output
        )
    
    return output


@click.group()
@click.version_option(version=__version__)
def cli():
    """Lintro - A unified CLI tool for code formatting, linting, and quality assurance."""
    pass


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    help="Comma-separated list of tools to run (default: all available tools)",
)
@click.option(
    "--exclude",
    help="Comma-separated list of patterns to exclude (in addition to default exclusions)",
)
@click.option(
    "--include-venv",
    is_flag=True,
    help="Include virtual environment directories (excluded by default)",
)
def check(paths: List[str], tools: Optional[str], exclude: Optional[str], include_venv: bool):
    """Check code for issues without fixing them."""
    if not paths:
        paths = [os.getcwd()]
    
    tool_list = parse_tool_list(tools)
    tools_to_run = {
        name: tool
        for name, tool in CHECK_TOOLS.items()
        if not tool_list or name in tool_list
    }
    
    if not tools_to_run:
        click.echo("No tools selected. Available tools: " + ", ".join(CHECK_TOOLS.keys()))
        sys.exit(1)
    
    # Process exclude patterns
    exclude_patterns = []
    if exclude:
        exclude_patterns = [p.strip() for p in exclude.split(",") if p.strip()]
    
    exit_code = 0
    results = []
    
    for name, tool in tools_to_run.items():
        print_tool_header(name, "check")
        
        # Modify tool command based on options
        if hasattr(tool, "set_options"):
            tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
        
        success, output = tool.check(list(paths))
        
        # Count issues and format output
        issues_count = count_issues(output, name)
        formatted_output = format_tool_output(output, name)
        click.echo(formatted_output)
        
        print_tool_footer(success, issues_count)
        
        results.append(ToolResult(name, success, output, issues_count))
        
        if not success:
            exit_code = 1
    
    print_summary(results, "check")
    sys.exit(exit_code)


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    help="Comma-separated list of tools to run (default: all tools that can fix)",
)
@click.option(
    "--exclude",
    help="Comma-separated list of patterns to exclude (in addition to default exclusions)",
)
@click.option(
    "--include-venv",
    is_flag=True,
    help="Include virtual environment directories (excluded by default)",
)
def fmt(paths: List[str], tools: Optional[str], exclude: Optional[str], include_venv: bool):
    """Format code and fix issues where possible."""
    if not paths:
        paths = [os.getcwd()]
    
    tool_list = parse_tool_list(tools)
    tools_to_run = {
        name: tool
        for name, tool in FIX_TOOLS.items()
        if not tool_list or name in tool_list
    }
    
    if not tools_to_run:
        click.echo("No tools selected. Available tools: " + ", ".join(FIX_TOOLS.keys()))
        sys.exit(1)
    
    # Process exclude patterns
    exclude_patterns = []
    if exclude:
        exclude_patterns = [p.strip() for p in exclude.split(",") if p.strip()]
    
    exit_code = 0
    results = []
    
    for name, tool in tools_to_run.items():
        print_tool_header(name, "fix")
        
        # Modify tool command based on options
        if hasattr(tool, "set_options"):
            tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
        
        success, output = tool.fix(list(paths))
        
        # Count issues and format output
        issues_count = count_issues(output, name)
        formatted_output = format_tool_output(output, name)
        click.echo(formatted_output)
        
        print_tool_footer(success, issues_count)
        
        results.append(ToolResult(name, success, output, issues_count))
        
        if not success:
            exit_code = 1
    
    print_summary(results, "format")
    sys.exit(exit_code)


@cli.command()
def list_tools():
    """List all available tools."""
    click.secho("Available tools:", bold=True)
    
    # Group tools by capability
    fix_tools = []
    check_only_tools = []
    
    for name, tool in sorted(AVAILABLE_TOOLS.items()):
        if tool.can_fix:
            fix_tools.append((name, tool))
        else:
            check_only_tools.append((name, tool))
    
    if fix_tools:
        click.secho("\nTools that can fix issues:", fg="green")
        for name, tool in fix_tools:
            click.echo(f"  - {name}: {tool.description}")
    
    if check_only_tools:
        click.secho("\nTools that can only check for issues:", fg="yellow")
        for name, tool in check_only_tools:
            click.echo(f"  - {name}: {tool.description}")


def main():
    """Entry point for the CLI."""
    cli() 