"""Command-line interface for Lintro."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, TextIO, Tuple

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


def print_tool_header(tool_name: str, action: str, file: Optional[TextIO] = None):
    """Print a header for a tool's output."""
    click.secho(f"\n{'=' * 60}", fg="blue", file=file)
    click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True, file=file)
    click.secho(f"{'=' * 60}", fg="blue", file=file)


def print_tool_footer(success: bool, issues_count: int, file: Optional[TextIO] = None):
    """Print a footer for a tool's output."""
    if success:
        click.secho(f"\n✓ No issues found", fg="green", file=file)
    else:
        click.secho(f"\n✗ Found {issues_count} issues", fg="red", file=file)
    click.secho(f"{'-' * 60}", fg="blue", file=file)


def print_summary(results: List[ToolResult], action: str, file: Optional[TextIO] = None):
    """Print a summary of all tool results."""
    total_issues = sum(result.issues_count for result in results)
    
    click.secho(f"\n{'=' * 60}", fg="yellow", file=file)
    click.secho(f" Summary ({action})", fg="yellow", bold=True, file=file)
    click.secho(f"{'=' * 60}", fg="yellow", file=file)
    
    for result in results:
        status = "✓" if result.success else "✗"
        color = "green" if result.success else "red"
        issues_text = "No issues" if result.issues_count == 0 else f"{result.issues_count} issues"
        click.secho(f" {status} {result.name}: {issues_text}", fg=color, file=file)
    
    click.secho(f"{'-' * 60}", fg="yellow", file=file)
    
    if total_issues == 0:
        click.secho(f" Total: No issues found", fg="green", file=file)
    else:
        click.secho(f" Total: {total_issues} issues found", fg="red", file=file)
    
    click.secho(f"{'=' * 60}", fg="yellow", file=file)


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
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file to write results to",
)
def check(paths: List[str], tools: Optional[str], exclude: Optional[str], include_venv: bool, output: Optional[str]):
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
    
    # Open output file if specified
    output_file = None
    if output:
        try:
            output_file = open(output, 'w')
            click.echo(f"Writing output to {output}")
        except IOError as e:
            click.echo(f"Error opening output file: {e}", err=True)
            sys.exit(1)
    
    try:
        exit_code = 0
        results = []
        
        for name, tool in tools_to_run.items():
            print_tool_header(name, "check", output_file)
            
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
            
            success, output_text = tool.check(list(paths))
            
            # Count issues and format output
            issues_count = count_issues(output_text, name)
            formatted_output = format_tool_output(output_text, name)
            click.echo(formatted_output, file=output_file)
            
            print_tool_footer(success, issues_count, output_file)
            
            results.append(ToolResult(name, success, output_text, issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "check", output_file)
        
        # If output file is specified, print a summary to the console as well
        if output_file:
            total_issues = sum(result.issues_count for result in results)
            if total_issues == 0:
                click.secho("No issues found", fg="green")
            else:
                click.secho(f"Found {total_issues} issues. See {output} for details.", fg="red")
        
        sys.exit(exit_code)
    finally:
        # Close the output file if it was opened
        if output_file:
            output_file.close()


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
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file to write results to",
)
def fmt(paths: List[str], tools: Optional[str], exclude: Optional[str], include_venv: bool, output: Optional[str]):
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
    
    # Open output file if specified
    output_file = None
    if output:
        try:
            output_file = open(output, 'w')
            click.echo(f"Writing output to {output}")
        except IOError as e:
            click.echo(f"Error opening output file: {e}", err=True)
            sys.exit(1)
    
    try:
        exit_code = 0
        results = []
        
        for name, tool in tools_to_run.items():
            print_tool_header(name, "fix", output_file)
            
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
            
            success, output_text = tool.fix(list(paths))
            
            # Count issues and format output
            issues_count = count_issues(output_text, name)
            formatted_output = format_tool_output(output_text, name)
            click.echo(formatted_output, file=output_file)
            
            print_tool_footer(success, issues_count, output_file)
            
            results.append(ToolResult(name, success, output_text, issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "format", output_file)
        
        # If output file is specified, print a summary to the console as well
        if output_file:
            total_issues = sum(result.issues_count for result in results)
            if total_issues == 0:
                click.secho("All files formatted successfully", fg="green")
            else:
                click.secho(f"Some files could not be formatted. See {output} for details.", fg="red")
        
        sys.exit(exit_code)
    finally:
        # Close the output file if it was opened
        if output_file:
            output_file.close()


@cli.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file to write results to",
)
def list_tools(output: Optional[str]):
    """List all available tools."""
    # Open output file if specified
    output_file = None
    if output:
        try:
            output_file = open(output, 'w')
            click.echo(f"Writing output to {output}")
        except IOError as e:
            click.echo(f"Error opening output file: {e}", err=True)
            sys.exit(1)
    
    try:
        click.secho("Available tools:", bold=True, file=output_file)
        
        # Group tools by capability
        fix_tools = []
        check_only_tools = []
        
        for name, tool in sorted(AVAILABLE_TOOLS.items()):
            if tool.can_fix:
                fix_tools.append((name, tool))
            else:
                check_only_tools.append((name, tool))
        
        if fix_tools:
            click.secho("\nTools that can fix issues:", fg="green", file=output_file)
            for name, tool in fix_tools:
                click.echo(f"  - {name}: {tool.description}", file=output_file)
        
        if check_only_tools:
            click.secho("\nTools that can only check for issues:", fg="yellow", file=output_file)
            for name, tool in check_only_tools:
                click.echo(f"  - {name}: {tool.description}", file=output_file)
    finally:
        # Close the output file if it was opened
        if output_file:
            output_file.close()


def main():
    """Entry point for the CLI."""
    cli() 