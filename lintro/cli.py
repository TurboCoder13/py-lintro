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
        # Count "ERROR:" lines for isort, but don't count skipped files as issues
        if "All imports are correctly sorted." in output:
            return 0
        return len(re.findall(r"ERROR:", output))
    elif tool_name == "flake8":
        # Count lines with error codes (e.g., E501, W291)
        return len(re.findall(r":\d+:\d+: [EWFN]\d{3} ", output))
    else:
        # Generic fallback: count lines that look like issues
        return len(re.findall(r"(error|warning|issue|problem)", output, re.IGNORECASE))


def print_tool_header(tool_name: str, action: str, file: Optional[TextIO] = None):
    """Print a header for a tool's output."""
    click.secho(f"\n{'=' * 60}", fg="blue")
    click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True)
    click.secho(f"{'=' * 60}", fg="blue")
    
    # Also write to file if specified
    if file:
        click.secho(f"\n{'=' * 60}", fg="blue", file=file)
        click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True, file=file)
        click.secho(f"{'=' * 60}", fg="blue", file=file)


def print_tool_footer(success: bool, issues_count: int, file: Optional[TextIO] = None):
    """Print a footer for a tool's output."""
    # Always use issues_count to determine success/failure
    if issues_count == 0:
        click.secho(f"\n✓ No issues found", fg="green")
        if file:
            click.secho(f"\n✓ No issues found", fg="green", file=file)
    else:
        click.secho(f"\n✗ Found {issues_count} issues", fg="red")
        if file:
            click.secho(f"\n✗ Found {issues_count} issues", fg="red", file=file)
    
    click.secho(f"{'-' * 60}", fg="blue")
    if file:
        click.secho(f"{'-' * 60}", fg="blue", file=file)


def print_summary(results: List[ToolResult], action: str, file: Optional[TextIO] = None):
    """Print a summary of all tool results."""
    total_issues = sum(result.issues_count for result in results)
    
    click.secho(f"\n{'=' * 60}", fg="blue")
    click.secho(f" Summary ({action})", fg="blue", bold=True)
    click.secho(f"{'=' * 60}", fg="blue")
    
    if file:
        click.secho(f"\n{'=' * 60}", fg="blue", file=file)
        click.secho(f" Summary ({action})", fg="blue", bold=True, file=file)
        click.secho(f"{'=' * 60}", fg="blue", file=file)
    
    for result in results:
        if result.issues_count == 0:
            status = click.style("✓", fg="green")
            message = click.style("No issues", fg="green")
        else:
            status = click.style("✗", fg="red")
            message = click.style(f"{result.issues_count} issues", fg="red")
        
        click.echo(f" {status} {result.name}: {message}")
        if file:
            click.echo(f" {status} {result.name}: {message}", file=file)
    
    click.secho(f"{'-' * 60}", fg="blue")
    if file:
        click.secho(f"{'-' * 60}", fg="blue", file=file)
    
    if total_issues == 0:
        status = click.style("✓", fg="green")
        message = click.style("No issues found", fg="green")
    else:
        status = click.style("✗", fg="red")
        message = click.style(f"{total_issues} issues found", fg="red")
    
    click.echo(f" Total: {message}")
    click.secho(f"{'=' * 60}", fg="blue")
    
    if file:
        click.echo(f" Total: {message}", file=file)
        click.secho(f"{'=' * 60}", fg="blue", file=file)


def parse_tool_list(tools_str: Optional[str]) -> List[str]:
    """Parse a comma-separated list of tool names."""
    if not tools_str:
        return []
    return [t.strip() for t in tools_str.split(",") if t.strip()]


# Add a function to get project-relative path
def get_relative_path(file_path: str) -> str:
    """Convert absolute path to project-relative path."""
    try:
        # Get the current working directory as the project root
        cwd = os.getcwd()
        
        # Check if the file path starts with the cwd
        if file_path.startswith(cwd):
            return "/project" + file_path[len(cwd):]
        
        # If not in cwd, try to find a common project indicator
        for indicator in ["src/", "tests/", "app/", "lib/"]:
            if indicator in file_path:
                parts = file_path.split(indicator, 1)
                return f"/project/{indicator}{parts[1]}"
        
        # If no project structure detected, use the basename
        return f"/project/{os.path.basename(file_path)}"
    except Exception:
        # Fallback to original path if any error occurs
        return file_path


def format_tool_output(output: str, tool_name: str) -> str:
    """Format the output of a tool to be more readable and standardized."""
    if not output:
        return "No output"
    
    # Remove trailing whitespace and ensure ending with newline
    output = output.rstrip() + "\n"
    
    # Standardize output format
    formatted_lines = []
    
    if tool_name == "black":
        # Extract file paths from Black output
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = line.replace("would reformat ", "").strip()
                rel_path = get_relative_path(file_path)
                # Convert to standardized format with color and alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<50}", fg="yellow") + 
                    click.style(f" : {'N/A':<8}", fg="blue") +
                    click.style(f" : {'FORMAT':<8}", fg="red") + 
                    f" : formatting required"
                )
            elif "All done!" in line or "Oh no!" in line or "files would be" in line:
                # Keep summary lines with color
                if "All done!" in line:
                    formatted_lines.append(click.style(line, fg="green"))
                else:
                    formatted_lines.append(click.style(line, fg="red"))
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)
    
    elif tool_name == "isort":
        # Extract file paths from isort output
        skipped_files = 0
        for line in output.splitlines():
            if "ERROR:" in line and ":" in line:
                parts = line.split(":", 1)
                file_path = parts[0].strip()
                rel_path = get_relative_path(file_path)
                # Convert to standardized format with color and alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<50}", fg="yellow") + 
                    click.style(f" : {'N/A':<8}", fg="blue") +
                    click.style(f" : {'ISORT':<8}", fg="red") + 
                    f" : import sorting required"
                )
            elif "Skipped" in line and "files" in line:
                # Count skipped files but don't include in issues
                skipped_match = re.search(r"Skipped (\d+) files", line)
                if skipped_match:
                    skipped_files = int(skipped_match.group(1))
                formatted_lines.append(click.style(f"Note: {line}", fg="blue"))
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)
        
        # If we only have skipped files and no actual errors, return success message
        if not formatted_lines and skipped_files > 0:
            return click.style("All imports are correctly sorted.", fg="green")
    
    elif tool_name == "flake8":
        # Extract and format flake8 errors
        for line in output.splitlines():
            # Match flake8 output format: file:line:col: code message
            match = re.match(r"(.+):(\d+):(\d+): ([A-Z]\d{3}) (.+)", line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                error_code = match.group(4)
                message = match.group(5)
                rel_path = get_relative_path(file_path)
                
                # Convert to standardized format with color and alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<50}", fg="yellow") + 
                    click.style(f" : {line_num:<8}", fg="blue") +
                    click.style(f" : {error_code:<8}", fg="red") + 
                    f" : {message}"
                )
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)
    
    else:
        # For other tools, keep the original output
        formatted_lines = output.splitlines()
    
    return "\n".join(formatted_lines) + "\n"


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
            
            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                click.echo(formatted_output, file=output_file)
            
            # Use issues_count to determine success
            success = issues_count == 0
            print_tool_footer(success, issues_count, output_file)
            
            results.append(ToolResult(name=name, success=success, output=output_text, issues_count=issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "check", output_file)
        
        # If output file is specified, print a summary to the console as well
        if output_file:
            total_issues = sum(result.issues_count for result in results)
            if total_issues == 0:
                click.secho("No issues found in your code.", fg="green")
            else:
                click.secho(f"Found {total_issues} issues in your code. See {output} for details.", fg="red")
        
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
            
            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                click.echo(formatted_output, file=output_file)
            
            # Use issues_count to determine success
            success = issues_count == 0
            print_tool_footer(success, issues_count, output_file)
            
            results.append(ToolResult(name=name, success=success, output=output_text, issues_count=issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "format", output_file)
        
        # If output file is specified, print a summary to the console as well
        if output_file:
            total_issues = sum(result.issues_count for result in results)
            if total_issues == 0:
                click.secho("All files formatted successfully.", fg="green")
            else:
                click.secho(f"Found {total_issues} issues while formatting. See {output} for details.", fg="red")
        
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
        # Display in console
        click.secho("Available tools:", bold=True)
        
        # Also write to file if specified
        if output_file:
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
            # Display in console
            click.secho("\nTools that can fix issues:", fg="green")
            for name, tool in fix_tools:
                click.echo(f"  - {name}: {tool.description}")
            
            # Also write to file if specified
            if output_file:
                click.secho("\nTools that can fix issues:", fg="green", file=output_file)
                for name, tool in fix_tools:
                    click.echo(f"  - {name}: {tool.description}", file=output_file)
        
        if check_only_tools:
            # Display in console
            click.secho("\nTools that can only check for issues:", fg="yellow")
            for name, tool in check_only_tools:
                click.echo(f"  - {name}: {tool.description}")
            
            # Also write to file if specified
            if output_file:
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