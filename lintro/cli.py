"""Command-line interface for Lintro."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import TextIO

import click
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

from lintro import __version__
from lintro.tools import AVAILABLE_TOOLS, CHECK_TOOLS, FIX_TOOLS


@dataclass
class ToolResult:
    """Result of running a tool."""
    name: str
    success: bool
    output: str
    issues_count: int = 0


def count_issues(
    output: str,
    tool_name: str,
) -> int:
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


def print_tool_header(
    tool_name: str,
    action: str,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """Print a header for a tool's output."""
    if not use_table_format:
        # Standard format
        click.secho(f"\n{'=' * 60}", fg="blue")
        click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True)
        click.secho(f"{'=' * 60}", fg="blue")
        
        # Also write to file if specified
        if file:
            click.secho(f"\n{'=' * 60}", fg="blue", file=file)
            click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True, file=file)
            click.secho(f"{'=' * 60}", fg="blue", file=file)
    else:
        # Table format
        header = f"\n{'-' * 60}\n Running {tool_name} ({action})\n{'-' * 60}"
        click.secho(header, fg="blue", bold=True)
        if file:
            click.secho(header, fg="blue", bold=True, file=file)


def print_tool_footer(
    success: bool,
    issues_count: int,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """Print a footer for a tool's output."""
    if not use_table_format:
        # Standard format
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
    else:
        # Table format
        if issues_count == 0:
            footer = f"\n✓ No issues found"
            click.secho(footer, fg="green")
            if file:
                click.secho(footer, fg="green", file=file)
        else:
            footer = f"\n✗ Found {issues_count} issues"
            click.secho(footer, fg="red")
            if file:
                click.secho(footer, fg="red", file=file)
        
        click.secho(f"{'-' * 60}", fg="blue")
        if file:
            click.secho(f"{'-' * 60}", fg="blue", file=file)


def print_summary(
    results: list[ToolResult],
    action: str,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """Print a summary of all tool results."""
    total_issues = sum(result.issues_count for result in results)
    
    if not use_table_format:
        # Standard format
        click.secho(f"\n{'=' * 60}", fg="blue")
        click.secho(f" Summary ({action})", fg="blue", bold=True)
        click.secho(f"{'=' * 60}", fg="blue")
        
        if file:
            click.secho(f"\n{'=' * 60}", fg="blue", file=file)
            click.secho(f" Summary ({action})", fg="blue", bold=True, file=file)
            click.secho(f"{'=' * 60}", fg="blue", file=file)
    else:
        # Table format
        header = f"\n{'-' * 60}\n Summary ({action})\n{'-' * 60}"
        click.secho(header, fg="blue", bold=True)
        if file:
            click.secho(header, fg="blue", bold=True, file=file)
    
    # Create a table for the summary if using table format
    if use_table_format and TABULATE_AVAILABLE:
        summary_data = []
        for result in results:
            status = "✓" if result.issues_count == 0 else "✗"
            status_color = "green" if result.issues_count == 0 else "red"
            message = "No issues" if result.issues_count == 0 else f"{result.issues_count} issues"
            
            summary_data.append([
                click.style(status, fg=status_color),
                result.name,
                click.style(message, fg=status_color)
            ])
        
        summary_table = tabulate(
            summary_data,
            headers=["Status", "Tool", "Result"],
            tablefmt="pretty",
            colalign=("left", "left", "left")  # Left align all columns
        )
        
        click.echo(summary_table)
        if file:
            click.echo(summary_table, file=file)
        
        # Add total line
        if total_issues == 0:
            total_line = click.style(f"\nTotal: No issues found", fg="green")
        else:
            total_line = click.style(f"\nTotal: {total_issues} issues found", fg="red")
        
        click.echo(total_line)
        if file:
            click.echo(total_line, file=file)
        
        click.secho(f"{'-' * 60}", fg="blue")
        if file:
            click.secho(f"{'-' * 60}", fg="blue", file=file)
    else:
        # Standard format for summary items
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


def parse_tool_list(tools_str: str | None) -> list[str]:
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
            # Return the path relative to the current directory without '/project' prefix
            return file_path[len(cwd) + 1:]  # +1 to remove the leading slash
        
        # If not in cwd, try to find a common project indicator
        for indicator in ["src/", "tests/", "app/", "lib/"]:
            if indicator in file_path:
                parts = file_path.split(indicator, 1)
                return f"{indicator}{parts[1]}"
        
        # If no project structure detected, use the basename
        return os.path.basename(file_path)
    except Exception:
        # Fallback to original path if any error occurs
        return file_path


# Add a function to format output as a table
def format_as_table(
    issues,
    tool_name=None,
    group_by="file",
):
    """Format issues as a table using tabulate if available.
    
    Args:
        issues: List of issue dictionaries
        tool_name: Name of the tool that found the issues
        group_by: How to group issues - 'file', 'code', 'none', or 'auto'
    """
    if not TABULATE_AVAILABLE:
        return None
    
    # Add tool name to the table if provided
    title = ""
    if tool_name:
        title = f"Results for {tool_name}:"
    
    # If there are no issues, return early
    if not issues:
        return title
    
    # Auto-determine the best grouping method if 'auto' is specified
    if group_by == "auto":
        # Count unique files and codes
        unique_files = len(set(issue["path"] for issue in issues))
        unique_codes = len(set(issue["code"] for issue in issues))
        
        # If there are more unique files than codes, group by code
        # This is more efficient when many files have the same few error types
        if unique_files > unique_codes and unique_codes <= 5:
            group_by = "code"
        else:
            group_by = "file"
    
    # Format based on grouping option
    result = []
    if title:
        result.append(title)
    
    # Define tool-specific table formats
    if tool_name == "black":
        # Black only needs file paths for formatting
        if group_by == "file":
            # Not applicable for Black - just list files
            for file_path in sorted(set(issue["path"] for issue in issues)):
                result.append(f"\nFile: {file_path}")
                result.append("  Formatting required")
        else:
            # For Black, we don't need to group by code since there's only one type of issue
            table_data = []
            for issue in issues:
                table_data.append([issue["path"]])
            
            headers = ["File"]
            
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left",)
            )
            
            result.append("\nFiles requiring formatting:")
            result.append(table)
    
    elif tool_name == "isort":
        # isort only needs file paths for import sorting
        if group_by == "file":
            # Not applicable for isort - just list files
            for file_path in sorted(set(issue["path"] for issue in issues)):
                result.append(f"\nFile: {file_path}")
                result.append("  Import sorting required")
        else:
            # For isort, we don't need to group by code since there's only one type of issue
            table_data = []
            for issue in sorted(issues, key=lambda x: x["path"]):
                if issue["path"] != "ERROR":  # Skip the ERROR placeholder
                    table_data.append([issue["path"]])
            
            headers = ["File"]
            
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left",)
            )
            
            result.append("\nFiles requiring import sorting:")
            result.append(table)
    
    elif tool_name == "flake8":
        # flake8 has detailed error codes and line numbers
        if group_by == "file":
            # Group by file
            issues_by_file = {}
            for issue in issues:
                file_path = issue["path"]
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
            
            for file_path, file_issues in sorted(issues_by_file.items()):
                # Add file header
                result.append(f"\nFile: {file_path}")
                
                # Convert issues to a list of lists for tabulate
                table_data = []
                for issue in file_issues:
                    table_data.append([
                        issue["line"],
                        issue["code"],
                        issue["message"]
                    ])
                
                # Format as a table with headers - use left alignment
                headers = ["Line", "PEP Code", "Message"]
                
                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left")
                )
                
                result.append(table)
        
        elif group_by == "code":
            # Group by error code
            issues_by_code = {}
            for issue in issues:
                code = issue["code"]
                if code not in issues_by_code:
                    issues_by_code[code] = []
                issues_by_code[code].append(issue)
            
            for code, code_issues in sorted(issues_by_code.items()):
                # Add code header
                result.append(f"\nPEP Code: {code}")
                
                # Convert issues to a list of lists for tabulate
                table_data = []
                for issue in code_issues:
                    table_data.append([
                        issue["path"],
                        issue["line"],
                        issue["message"]
                    ])
                
                # Format as a table with headers - use left alignment
                headers = ["File", "Line", "Message"]
                
                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left")
                )
                
                result.append(table)
        
        else:  # No grouping
            # Convert issues to a list of lists for tabulate
            table_data = []
            for issue in issues:
                table_data.append([
                    issue["path"],
                    issue["line"],
                    issue["code"],
                    issue["message"]
                ])
            
            # Format as a table with headers - use left alignment
            headers = ["File", "Line", "PEP Code", "Message"]
            
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left", "left", "left", "left")
            )
            
            result.append(table)
    
    else:
        # Generic format for other tools
        if group_by == "file":
            # Group by file
            issues_by_file = {}
            for issue in issues:
                file_path = issue["path"]
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
            
            for file_path, file_issues in sorted(issues_by_file.items()):
                # Add file header
                result.append(f"\nFile: {file_path}")
                
                # Convert issues to a list of lists for tabulate
                table_data = []
                for issue in file_issues:
                    table_data.append([
                        issue["line"],
                        issue["code"],
                        issue["message"]
                    ])
                
                # Format as a table with headers - use left alignment
                headers = ["Line", "Code", "Message"]
                
                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left")
                )
                
                result.append(table)
        
        elif group_by == "code":
            # Group by error code
            issues_by_code = {}
            for issue in issues:
                code = issue["code"]
                if code not in issues_by_code:
                    issues_by_code[code] = []
                issues_by_code[code].append(issue)
            
            for code, code_issues in sorted(issues_by_code.items()):
                # Add code header
                result.append(f"\nCode: {code}")
                
                # Convert issues to a list of lists for tabulate
                table_data = []
                for issue in code_issues:
                    table_data.append([
                        issue["path"],
                        issue["line"],
                        issue["message"]
                    ])
                
                # Format as a table with headers - use left alignment
                headers = ["File", "Line", "Message"]
                
                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left")
                )
                
                result.append(table)
        
        else:  # No grouping
            # Convert issues to a list of lists for tabulate
            table_data = []
            for issue in issues:
                table_data.append([
                    issue["path"],
                    issue["line"],
                    issue["code"],
                    issue["message"]
                ])
            
            # Format as a table with headers - use left alignment
            headers = ["File", "Line", "Code", "Message"]
            
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left", "left", "left", "left")
            )
            
            result.append(table)
    
    return "\n".join(result)


def format_tool_output(
    output: str,
    tool_name: str,
    use_table_format: bool = False,
    group_by: str = "file",
) -> str:
    """Format the output of a tool to be more readable and standardized."""
    if not output:
        return "No output"
    
    # Remove trailing whitespace and ensure ending with newline
    output = output.rstrip() + "\n"
    
    # Standardize output format
    formatted_lines = []
    issues = []
    
    # First pass to collect all file paths for determining optimal column width
    file_paths = []
    line_numbers = []
    error_codes = []
    
    if tool_name == "black":
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = line.replace("would reformat ", "").strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("FORMAT")
                
                # Add to issues list for table formatting
                issues.append({
                    "path": rel_path,
                    "line": "N/A",
                    "code": "FORMAT",
                    "message": "formatting required"
                })
    
    elif tool_name == "isort":
        # Extract file paths from isort output
        skipped_files = 0
        for line in output.splitlines():
            # Match the actual isort output format: "ERROR: /path/to/file.py Imports are incorrectly sorted..."
            match = re.match(r"ERROR: (.*?) Imports are incorrectly sorted", line)
            if match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("ISORT")
                
                # Add to issues list for table formatting
                issues.append({
                    "path": rel_path,
                    "line": "N/A",
                    "code": "ISORT",
                    "message": "import sorting required"
                })
            elif "Skipped" in line and "files" in line:
                # Count skipped files but don't include in issues
                skipped_match = re.search(r"Skipped (\d+) files", line)
                if skipped_match:
                    skipped_files = int(skipped_match.group(1))
        
        # If we only have skipped files and no actual errors, return success message
        if not file_paths and skipped_files > 0:
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
                
                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)
                
                # Add to issues list for table formatting
                issues.append({
                    "path": rel_path,
                    "line": line_num,
                    "code": error_code,
                    "message": message
                })
    
    # If tabulate is available, table format is requested, and we have issues, format as a table
    if TABULATE_AVAILABLE and use_table_format and issues:
        table = format_as_table(issues, tool_name, group_by)
        if table:
            # Add any summary lines
            if tool_name == "black":
                for line in output.splitlines():
                    if "All done!" in line or "Oh no!" in line or "files would be" in line:
                        if "All done!" in line:
                            table += "\n" + click.style(line, fg="green")
                        else:
                            table += "\n" + click.style(line, fg="red")
            
            # Add any skipped files notes for isort
            if tool_name == "isort" and skipped_files > 0:
                table += "\n" + click.style(f"Note: Skipped {skipped_files} files", fg="blue")
            
            return table
    
    # Calculate optimal column widths (min 10, max 60)
    path_width = max([len(p) for p in file_paths] + [10]) if file_paths else 30
    path_width = min(path_width + 2, 60)  # Add some padding but cap at 60
    
    line_width = max([len(l) for l in line_numbers] + [4]) if line_numbers else 6
    line_width = min(line_width + 2, 10)  # Add some padding but cap at 10
    
    code_width = max([len(c) for c in error_codes] + [6]) if error_codes else 8
    code_width = min(code_width + 2, 12)  # Add some padding but cap at 12
    
    # Second pass to format with calculated widths
    if tool_name == "black":
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = line.replace("would reformat ", "").strip()
                rel_path = get_relative_path(file_path)
                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow") + 
                    click.style(f" : {'N/A':<{line_width}}", fg="blue") +
                    click.style(f" : {'FORMAT':<{code_width}}", fg="red") + 
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
        for line in output.splitlines():
            if "ERROR:" in line and ":" in line:
                parts = line.split(":", 1)
                file_path = parts[0].strip()
                rel_path = get_relative_path(file_path)
                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow") + 
                    click.style(f" : {'N/A':<{line_width}}", fg="blue") +
                    click.style(f" : {'ISORT':<{code_width}}", fg="red") + 
                    f" : import sorting required"
                )
            elif "Skipped" in line and "files" in line:
                # Count skipped files but don't include in issues
                formatted_lines.append(click.style(f"Note: {line}", fg="blue"))
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)
    
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
                
                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow") + 
                    click.style(f" : {line_num:<{line_width}}", fg="blue") +
                    click.style(f" : {error_code:<{code_width}}", fg="red") + 
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
@click.option(
    "--table-format",
    is_flag=True,
    help="Use table formatting for output (requires tabulate package)",
)
@click.option(
    "--group-by",
    type=click.Choice(["file", "code", "none", "auto"]),
    default="auto",
    help="How to group issues in the output (file, code, none, or auto)",
)
def check(
    paths: list[str],
    tools: str | None,
    exclude: str | None,
    include_venv: bool,
    output: str | None,
    table_format: bool,
    group_by: str,
):
    """Check code for issues without fixing them."""
    if not paths:
        paths = [os.getcwd()]
    
    # Check if table format is requested but tabulate is not available
    if table_format and not TABULATE_AVAILABLE:
        click.echo("Warning: Table formatting requested but tabulate package is not installed.", err=True)
        click.echo("Install with: pip install tabulate", err=True)
        table_format = False
    
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
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
            
            print_tool_header(name, "check", output_file, table_format)
            
            success, output_text = tool.check(list(paths))
            
            # Count issues and format output
            issues_count = count_issues(output_text, name)
            formatted_output = format_tool_output(output_text, name, table_format, group_by)
            
            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                # Use the same formatted output for the file to ensure consistency
                click.echo(formatted_output, file=output_file)
            
            # Use issues_count to determine success
            success = issues_count == 0
            print_tool_footer(success, issues_count, output_file, table_format)
            
            results.append(ToolResult(name=name, success=success, output=output_text, issues_count=issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "check", output_file, table_format)
        
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
@click.option(
    "--table-format",
    is_flag=True,
    help="Use table formatting for output (requires tabulate package)",
)
@click.option(
    "--group-by",
    type=click.Choice(["file", "code", "none", "auto"]),
    default="auto",
    help="How to group issues in the output (file, code, none, or auto)",
)
def fmt(
    paths: list[str],
    tools: str | None,
    exclude: str | None,
    include_venv: bool,
    output: str | None,
    table_format: bool,
    group_by: str,
):
    """Format code and fix issues where possible."""
    if not paths:
        paths = [os.getcwd()]
    
    # Check if table format is requested but tabulate is not available
    if table_format and not TABULATE_AVAILABLE:
        click.echo("Warning: Table formatting requested but tabulate package is not installed.", err=True)
        click.echo("Install with: pip install tabulate", err=True)
        table_format = False
    
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
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(exclude_patterns=exclude_patterns, include_venv=include_venv)
            
            print_tool_header(name, "fix", output_file, table_format)
            
            success, output_text = tool.fix(list(paths))
            
            # Count issues and format output
            issues_count = count_issues(output_text, name)
            formatted_output = format_tool_output(output_text, name, table_format, group_by)
            
            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                # Use the same formatted output for the file to ensure consistency
                click.echo(formatted_output, file=output_file)
            
            # Use issues_count to determine success
            success = issues_count == 0
            print_tool_footer(success, issues_count, output_file, table_format)
            
            results.append(ToolResult(name=name, success=success, output=output_text, issues_count=issues_count))
            
            if not success:
                exit_code = 1
        
        print_summary(results, "format", output_file, table_format)
        
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
def list_tools(output: str | None):
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