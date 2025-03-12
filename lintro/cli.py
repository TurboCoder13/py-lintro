"""Command-line interface for Lintro."""

import os
import re
import sys
from dataclasses import dataclass
from typing import TextIO

import click
import subprocess
import random
import time
from pathlib import Path

try:
    from tabulate import tabulate

    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

from lintro import __version__
from lintro.tools import (
    AVAILABLE_TOOLS,
    CHECK_TOOLS,
    FIX_TOOLS,
    get_tool_execution_order,
)


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
    """
    Count the number of issues in the tool output.

    Args:
        output: The output from the tool
        tool_name: The name of the tool

    Returns:
        Number of issues found in the output
    """
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
    elif tool_name == "darglint":
        # Count lines with darglint error codes (e.g., DAR101, DAR201)
        # Also count skipped files as issues
        dar_issues = len(re.findall(r"DAR\d{3}", output))
        skipped_files = 0
        match = re.search(r"Skipped (\d+) files due to timeout", output)
        if match:
            skipped_files = int(match.group(1))
        return dar_issues + skipped_files
    elif tool_name == "hadolint":
        # Count lines with hadolint error codes (e.g., DL3000, SC2086)
        return len(re.findall(r"(DL\d{4}|SC\d{4})", output))
    elif tool_name == "pydocstyle":
        # Count lines with pydocstyle error codes (e.g., D100, D101)
        return len(re.findall(r"D\d{3}", output))
    elif tool_name == "prettier":
        # Count "[warn]" lines for prettier
        if "All files are formatted correctly." in output:
            return 0
        # Count the number of files that would be formatted
        return len(re.findall(r"would be formatted", output))
    elif tool_name == "pylint":
        # Count lines with pylint message codes (e.g., C0103, E0611)
        return len(re.findall(r"[CEFIRW]\d{4}", output))
    elif tool_name == "semgrep":
        # Count occurrences of the semgrep rule indicator
        return len(re.findall(r"❯❯❱", output))
    elif tool_name == "terraform":
        # Count formatting issues and validation errors
        fmt_issues = len(re.findall(r"[-+]", output))
        validation_issues = len(re.findall(r"\[ERROR\]", output))
        return fmt_issues + validation_issues
    elif tool_name == "yamllint":
        # Count lines with yamllint issues (format: file:line:column: [level] message)
        return len(re.findall(r":\d+:\d+: \[(error|warning)\]", output))
    else:
        # Generic fallback: count lines that look like issues
        return len(re.findall(r"(error|warning|issue|problem)", output, re.IGNORECASE))


def get_tool_emoji(tool_name: str) -> str:
    """
    Get an emoji for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Emoji for the tool
    """
    emojis = {
        "black": "🖤",
        "isort": "📋",
        "flake8": "❄️",
        "darglint": "📝",
        "hadolint": "🐳",
        "prettier": "💅",
        "pydocstyle": "📄",
        "pylint": "🔍",
        "semgrep": "🔒",
        "terraform": "🏗️",
        "yamllint": "📐",
    }
    return emojis.get(tool_name, "🔧")


def print_tool_header(
    tool_name: str,
    action: str,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """
    Print a header for a tool's output.

    Args:
        tool_name: Name of the tool
        action: Action being performed (check or fix)
        file: File to write to (default: stdout)
        use_table_format: Whether to use table formatting
    """
    # Get emoji for the tool
    emoji = get_tool_emoji(tool_name)
    
    # Create a decorative header with the tool name
    emojis = f"{emoji} {emoji} {emoji} {emoji} {emoji}"
    tool_info = f"✨  Running {tool_name} ({action})"
    border = "=" * 70
    
    # Format the header
    formatted_header = f"{border}\n{tool_info}    {emojis}\n{border}\n"
    
    # Output to console and file if specified
    click.echo(formatted_header, file=None)
    if file:
        click.echo(formatted_header, file=file)


def print_tool_footer(
    success: bool,
    issues_count: int,
    file: TextIO | None = None,
    use_table_format: bool = False,
    tool_name: str = "",
):
    """
    Print a footer for a tool's output.

    Args:
        success: Whether the tool ran successfully
        issues_count: Number of issues found
        file: File to write to (default: stdout)
        use_table_format: Whether to use table formatting
        tool_name: Name of the tool
    """
    # Create a message based on the number of issues
    if issues_count == 0:
        status = click.style("✓", fg="green", bold=True)
        message = click.style("No issues found", fg="green", bold=True)
    else:
        status = click.style("✗", fg="red", bold=True)
        issue_text = "issue" if issues_count == 1 else "issues"
        message = click.style(f"Found {issues_count} {issue_text}", fg="red", bold=True)
    
    # Format the footer
    formatted_footer = f"\n{status} {message}\n\n"
    
    # Output to console and file if specified
    click.echo(formatted_footer, file=None)
    if file:
        click.echo(formatted_footer, file=file)


def read_ascii_art(filename: str) -> list[str]:
    """
    Read ASCII art from a file.

    Args:
        filename: Name of the file to read

    Returns:
        List of lines from the file
    """
    # Get the path to the ASCII art file
    ascii_art_dir = Path(__file__).parent / "ascii-art"
    file_path = ascii_art_dir / filename
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read all lines and remove trailing whitespace
            lines = [line.rstrip() for line in f.readlines()]
            
            # Find non-empty sections (separated by empty lines)
            sections = []
            current_section = []
            
            for line in lines:
                if line.strip():
                    current_section.append(line)
                elif current_section:
                    sections.append(current_section)
                    current_section = []
            
            # Add the last section if it's not empty
            if current_section:
                sections.append(current_section)
            
            # Return a random section if there are multiple, otherwise return all lines
            if sections:
                return random.choice(sections)
            return lines
    except Exception as e:
        # If there's an error reading the file, return an empty list
        click.echo(f"Error reading ASCII art file: {e}", err=True)
        return []


def print_summary(
    results: list[ToolResult],
    action: str,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """
    Print a summary of the results.

    Args:
        results: List of tool results
        action: Action that was performed (check or fix)
        file: File to write to (default: stdout)
        use_table_format: Whether to use table formatting
    """
    # Count total issues
    total_issues = sum(result.issues_count for result in results)
    
    # Create a summary header
    border = "=" * 70
    summary_title = f"📊  Summary of {action}"
    emojis = "📊 📊 📊 📊 📊"
    
    # Format the summary header
    header = f"{border}\n{summary_title}    {emojis}\n{border}\n"
    
    # Format the summary
    if use_table_format:
        # First, generate a properly formatted table without colors
        table_data = []
        
        # Prepare data for tabulate
        for result in results:
            tool_name = result.name
            # A tool is successful if it has 0 issues, regardless of the original success flag
            is_successful = result.issues_count == 0
            status = "✓" if is_successful else "✗"
            issues_count = str(result.issues_count)
            table_data.append([tool_name, status, issues_count])
        
        # Generate the table
        table = tabulate(
            table_data,
            headers=["Tool", "Status", "Issues"],
            tablefmt="grid",
            colalign=("left", "center", "center"),
        )
        
        # Now add colors by processing the table line by line
        colored_lines = []
        for line in table.split('\n'):
            # Skip lines that don't contain data
            if '|' not in line or all(c in '+|-=' for c in line.replace(' ', '')):
                colored_lines.append(line)
                continue
                
            # Process header line
            if "Tool" in line and "Status" in line and "Issues" in line:
                colored_lines.append(click.style(line, bold=True))
                continue
                
            # Process data lines - we need to find and replace the status and issues
            parts = line.split('|')
            if len(parts) >= 4:  # Should have at least 4 parts with our table format
                # Keep the tool name as is
                tool_part = parts[1]
                
                # Color the status
                status_part = parts[2]
                if "✓" in status_part:
                    colored_status = status_part.replace("✓", click.style("✓", fg="green", bold=True))
                else:
                    colored_status = status_part.replace("✗", click.style("✗", fg="red", bold=True))
                
                # Color the issues
                issues_part = parts[3]
                issues_value = issues_part.strip()
                if issues_value == "0":
                    colored_issues = issues_part.replace("0", click.style("0", fg="green"))
                elif issues_value.isdigit() and int(issues_value) <= 10:
                    colored_issues = issues_part.replace(issues_value, click.style(issues_value, fg="yellow"))
                else:
                    colored_issues = issues_part.replace(issues_value, click.style(issues_value, fg="red"))
                
                # Reconstruct the line with colored parts
                colored_line = "|" + tool_part + "|" + colored_status + "|" + colored_issues + "|"
                colored_lines.append(colored_line)
            else:
                colored_lines.append(line)
        
        # Join the colored lines
        colored_table = '\n'.join(colored_lines)
        
        # Add a fun line based on the total number of issues
        if total_issues == 0:
            fun_line = click.style("🎉 No issues found! Your code is looking great! 🎉", fg="green", bold=True)
        elif total_issues < 10:
            fun_line = click.style("🔨 A few issues to fix, but you're almost there! 💪", fg="yellow", bold=True)
        else:
            fun_line = click.style("🧹 Time for some cleanup! Let's make this code shine! ✨", fg="red", bold=True)
        
        # Get ASCII art based on the results
        if total_issues == 0:
            ascii_art = read_ascii_art("success.txt")
        else:
            ascii_art = read_ascii_art("fail.txt")
        
        # Format the ASCII art
        ascii_art_text = "\n".join(ascii_art) if ascii_art else ""
        
        # Format the summary with ASCII art
        summary = f"{header}{colored_table}\n\n{fun_line}\n\n{ascii_art_text}\n"
    else:
        # Create a simple summary
        summary_lines = []
        for result in results:
            emoji = get_tool_emoji(result.name)
            # A tool is successful if it has 0 issues, regardless of the original success flag
            is_successful = result.issues_count == 0
            if is_successful:
                status = click.style("✓", fg="green", bold=True)
            else:
                status = click.style("✗", fg="red", bold=True)
            
            if result.issues_count > 0:
                issues_str = click.style(f"({result.issues_count} issues)", fg="red" if result.issues_count > 10 else "yellow")
            else:
                issues_str = click.style("(0 issues)", fg="green")
                
            summary_lines.append(f"{emoji} {result.name}: {status} {issues_str}")
        
        total_issues_str = click.style(f"Total issues: {total_issues}", bold=True, 
                                      fg="green" if total_issues == 0 else "red")
        summary_lines.append(total_issues_str)
        summary_text = "\n".join(summary_lines)
        
        # Get ASCII art based on the results
        if total_issues == 0:
            ascii_art = read_ascii_art("success.txt")
        else:
            ascii_art = read_ascii_art("fail.txt")
        
        # Format the ASCII art
        ascii_art_text = "\n".join(ascii_art) if ascii_art else ""
        
        # Format the summary with ASCII art
        summary = f"{header}{summary_text}\n\n{ascii_art_text}\n"
    
    # Output to console and file if specified
    click.echo(summary, file=None)
    if file:
        click.echo(summary, file=file)


def parse_tool_list(tools_str: str | None) -> list[str]:
    """
    Parse a comma-separated list of tool names.

    Args:
        tools_str: Comma-separated string of tool names

    Returns:
        List of individual tool names
    """
    if not tools_str:
        return []
    return [t.strip() for t in tools_str.split(",") if t.strip()]


def get_relative_path(file_path: str) -> str:
    """
    Convert an absolute path to a path relative to the current working directory.

    Args:
        file_path: Absolute file path

    Returns:
        Path relative to the current working directory
    """
    cwd = os.getcwd()
    if file_path.startswith(cwd):
        return file_path[len(cwd) + 1 :]
    return file_path


def get_table_columns(
    issues: list[dict],
    tool_name: str,
    group_by: str,
) -> tuple[list[str], list[str]]:
    """
    Determine which columns to include in the table based on the data.

    Args:
        issues: List of issues to format
        tool_name: Name of the tool that generated the issues
        group_by: How the issues are grouped (file, code, none)

    Returns:
        Tuple of (display_columns, code_columns) where:
        - display_columns: List of column headers to display
        - code_columns: List of keys for code columns used in grouping
    """
    # Define code column names based on tool
    if tool_name == "flake8":
        code_column = "PEP Code"
    elif tool_name in ["darglint", "pydocstyle"]:
        code_column = "Docstring Code"
    elif tool_name == "hadolint":
        code_column = "Dockerfile Code"
    elif tool_name == "pylint":
        code_column = "Pylint Code"
    elif tool_name == "semgrep":
        code_column = "Rule ID"
    elif tool_name == "terraform":
        code_column = "Issue Type"
    elif tool_name == "yamllint":
        code_column = "YAML Rule"
    else:
        code_column = "Code"

    # Define all possible columns and their corresponding keys in the issues dict
    columns_map = {
        "File": "file",
        code_column: "code",
        "Line": "line",
        "Method": "method",
        "Message": "message"
    }
    
    # Special case for Black: remove the Code column since it's always "FORMAT"
    if tool_name == "black":
        columns_map = {
            "File": "file",
            "Line": "line",
            "Message": "message"
        }
    
    # Add pylint-specific columns
    if tool_name == "pylint":
        # Insert Position right after Line
        columns_map = {
            "File": "file",
            code_column: "code",
            "Line": "line",
            "Position": "col",
            "Message": "message",
            "Name": "name"
        }

    # Add semgrep-specific columns
    if tool_name == "semgrep":
        columns_map = {
            "File": "file",
            code_column: "code",
            "Line": "line",
            "Position": "col",
            "Severity": "severity",
            "Message": "message",
        }

    # Add terraform-specific columns
    if tool_name == "terraform":
        columns_map = {
            "File": "file",
            code_column: "code",
            "Line": "line",
            "Severity": "severity",
            "Message": "message",
        }

    # Add yamllint-specific columns
    if tool_name == "yamllint":
        columns_map = {
            "File": "file",
            code_column: "code",
            "Line": "line",
            "Column": "col",
            "Severity": "severity",
            "Message": "message",
        }

    # Determine which columns to include based on grouping
    if group_by == "file":
        # When grouped by file, exclude the file column
        columns_to_check = {k: v for k, v in columns_map.items() if k != "File"}
    elif group_by == "code" and code_column in columns_map:
        # When grouped by code, exclude the code column
        columns_to_check = {k: v for k, v in columns_map.items() if k != code_column}
    else:
        # No grouping, include all columns
        columns_to_check = columns_map.copy()

    # Check which columns have meaningful values
    columns_to_include = []
    
    for header, key in columns_to_check.items():
        # Check if any issue has a meaningful value for this column
        has_values = False
        for issue in issues:
            if key in issue and issue[key] and issue[key] != "N/A":
                has_values = True
                break
                
        # Special case for darglint method column
        if key == "method" and tool_name == "darglint":
            has_values = True
            
        if has_values:
            columns_to_include.append(header)
    
    # Always include message column
    if "Message" not in columns_to_include:
        columns_to_include.append("Message")
        
    # Get the keys corresponding to the headers
    display_columns = columns_to_include
    
    # Return the list of code column names for grouping
    code_columns = ["code"]
    
    return display_columns, code_columns


def format_as_table(
    issues: list[dict],
    tool_name: str | None = None,
    group_by: str = "file",
) -> str:
    """
    Format issues as a table.

    Args:
        issues: List of issues to format
        tool_name: Name of the tool that produced the issues
        group_by: How to group issues (file, code, or none)

    Returns:
        Formatted table as a string
    """
    if not issues:
        return ""

    # Get columns to display based on the data
    display_columns, code_columns = get_table_columns(issues, tool_name or "", group_by)

    # Create a list to store all table rows
    all_rows = []

    # Define column mapping based on tool
    if tool_name == "flake8":
        code_key = "code"
    elif tool_name in ["darglint", "pydocstyle"]:
        code_key = "code"
    elif tool_name == "hadolint":
        code_key = "code"
    elif tool_name == "pylint":
        code_key = "code"
    elif tool_name == "semgrep":
        code_key = "code"
    else:
        code_key = "code"

    # Map display column headers to issue keys
    column_map = {
        "File": "file",
        "PEP Code": "code",
        "Docstring Code": "code",
        "Dockerfile Code": "code",
        "Pylint Code": "code",
        "Rule ID": "code",
        "Code": "code",
        "Line": "line",
        "Position": "col",
        "Method": "method",
        "Message": "message",
        "Name": "name",
        "Severity": "severity",
    }

    # Group issues by file or code if requested
    if group_by == "file" and "file" in issues[0]:
        # Get unique files and sort them
        files = sorted(set(issue["file"] for issue in issues))
        
        for file_idx, file in enumerate(files):
            # Add a file header
            file_issues = [issue for issue in issues if issue["file"] == file]
            
            # Add a separator between files (except before the first one)
            if file_idx > 0:
                all_rows.append(["~" * 80] + [""] * (len(display_columns) - 1))
            
            # Add file header with appropriate emoji based on issue severity
            has_error = any(issue.get("type") == "error" for issue in file_issues)
            has_warning = any(issue.get("type") == "warning" for issue in file_issues)
            
            if has_error:
                file_emoji = "🔴"  # Red circle for errors
            elif has_warning:
                file_emoji = "🟡"  # Yellow circle for warnings
            else:
                file_emoji = "🔵"  # Blue circle for info/other
                
            all_rows.append([f"{file_emoji} File: {file}"] + [""] * (len(display_columns) - 1))
            
            # Add the issues for this file
            for issue in file_issues:
                row = []
                for col in display_columns:
                    key = column_map.get(col)
                    if key and key in issue:
                        row.append(str(issue[key]))
                    else:
                        row.append("")
                all_rows.append(row)
                
    elif group_by == "code" and code_key in issues[0]:
        # Get unique codes and sort them
        codes = sorted(set(issue[code_key] for issue in issues if code_key in issue))
        
        for code_idx, code in enumerate(codes):
            # Add a separator between codes (except before the first one)
            if code_idx > 0:
                all_rows.append(["~" * 80] + [""] * (len(display_columns) - 1))
            
            # Add code header with appropriate emoji based on code
            if tool_name == "flake8":
                # For flake8, use different emojis based on the error code prefix
                if code.startswith("E"):
                    code_emoji = "🔴"  # Red circle for errors
                elif code.startswith("W"):
                    code_emoji = "🟡"  # Yellow circle for warnings
                elif code.startswith("F"):
                    code_emoji = "⚫"  # Black circle for fatal errors
                else:
                    code_emoji = "🔵"  # Blue circle for other
            elif tool_name == "pydocstyle":
                code_emoji = "📚"  # Books for documentation
            else:
                code_emoji = "🔍"  # Magnifying glass for generic codes
            
            # Get the appropriate code column name
            if tool_name == "flake8":
                code_column = "PEP Code"
            elif tool_name in ["darglint", "pydocstyle"]:
                code_column = "Docstring Code"
            elif tool_name == "hadolint":
                code_column = "Dockerfile Code"
            else:
                code_column = "Code"
                
            all_rows.append([f"{code_emoji} {code_column}: {code}"] + [""] * (len(display_columns) - 1))
            
            # Add the issues for this code
            code_issues = [issue for issue in issues if code_key in issue and issue[code_key] == code]
            for issue in code_issues:
                row = []
                for col in display_columns:
                    key = column_map.get(col)
                    if key and key in issue:
                        row.append(str(issue[key]))
                    else:
                        row.append("")
                all_rows.append(row)
    else:
        # No grouping, just add all issues
        for issue in issues:
            row = []
            for col in display_columns:
                key = column_map.get(col)
                if key and key in issue:
                    row.append(str(issue[key]))
                else:
                    row.append("")
            all_rows.append(row)

    # Format the table with left alignment for all columns
    colalign = tuple("left" for _ in display_columns)
    table = tabulate(
        all_rows,
        headers=display_columns,
        tablefmt="pretty",
        colalign=colalign,
    )

    # Add spacing before and after the table
    table = "\n" + table + "\n"

    # Add any summary lines for black
    if tool_name == "black" and "Oh no!" in "".join(str(issue.get("message", "")) for issue in issues):
        for issue in issues:
            if "message" in issue and "Formatting required" in issue["message"]:
                count = len([i for i in issues if "message" in i and "Formatting required" in i["message"]])
                table += f"\nOh no! 💥 💔 💥\n{count} files would be reformatted."

    return table


def format_tool_output(
    output: str,
    tool_name: str,
    use_table_format: bool = False,
    group_by: str = "file",
) -> str:
    """
    Format the output from a tool.

    Args:
        output: Raw output from the tool
        tool_name: Name of the tool
        use_table_format: Whether to use table formatting
        group_by: How to group the issues (file, code, none, or auto)

    Returns:
        Formatted output as a string
    """
    if not output:
        return "No output"

    # Special case for "No issues found" messages
    if (output.strip() == "No docstring issues found." or 
        output.strip() == "No Dockerfile issues found." or
        output.strip() == "No docstring style issues found." or
        output.strip() == "All files are formatted correctly." or
        output.strip() == "No Terraform issues found." or
        output.strip() == "No YAML issues found."):
        return output

    # Remove trailing whitespace and ensure ending with newline
    output = output.rstrip() + "\n"

    # Standardize output format
    formatted_lines = []
    issues = []

    # First pass to collect all file paths for determining optimal column width
    file_paths = []
    line_numbers = []
    error_codes = []
    skipped_files = 0

    if tool_name == "black":
        # Handle the "Oh no!" message separately
        if "Oh no!" in output:
            # Extract the number of files that would be reformatted
            match = re.search(r"(\d+) files? would be reformatted", output)
            if match:
                num_files = int(match.group(1))
                # Extract actual file paths if available
                file_paths = []
                for line in output.splitlines():
                    if "would reformat" in line:
                        file_path = line.replace("would reformat ", "").strip()
                        rel_path = get_relative_path(file_path)
                        file_paths.append(rel_path)
                
                # If we have actual file paths, use them
                if file_paths:
                    for file_path in file_paths:
                        issues.append({
                            "file": file_path,
                            "code": "FORMAT",
                            "line": "N/A",
                            "message": "Formatting required"
                        })
                else:
                    # Otherwise use placeholders
                    for i in range(num_files):
                        issues.append({
                            "file": f"File {i+1}",
                            "code": "FORMAT",
                            "line": "N/A",
                            "message": "Formatting required"
                        })
                
                # Extract the summary line
                summary_line = ""
                for line in output.splitlines():
                    if "files would be reformatted" in line and "files would be left unchanged" in line:
                        summary_line = line
                        break
                
                # Return the formatted table with just the summary line
                if use_table_format:
                    if summary_line:
                        return format_as_table(issues, tool_name, group_by) + f"\n{summary_line}"
                    else:
                        return format_as_table(issues, tool_name, group_by)
                return output
        
        # Normal processing for black output
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = line.replace("would reformat ", "").strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("FORMAT")

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": "FORMAT",
                    "line": "N/A",
                    "message": "Formatting required"
                })

    elif tool_name == "isort":
        # Extract file paths from isort output
        for line in output.splitlines():
            # Match the actual isort output format: "ERROR: /path/to/file.py Imports are incorrectly sorted..."
            match = re.match(r"ERROR: (.*?) Imports are incorrectly sorted", line)
            if match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("SORT")

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": "SORT",
                    "line": "N/A",
                    "message": "Imports are incorrectly sorted"
                })
            elif "Skipped" in line and "files" in line:
                # Count skipped files but don't include in issues
                match = re.search(r"Skipped (\d+) files", line)
                if match:
                    skipped_files = int(match.group(1))
                    # Add a note about skipped files
                    if use_table_format:
                        return "Note: Skipped " + match.group(1) + " files"

    elif tool_name == "flake8":
        # Extract file paths, line numbers, and error codes from flake8 output
        for line in output.splitlines():
            # Match the flake8 output format: "/path/to/file.py:123:45: E123 message"
            match = re.match(r"(.*?):(\d+):(\d+): ([A-Z]\d+) (.*)", line)
            if match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                line_num = match.group(2)
                error_code = match.group(4)
                message = match.group(5).strip()
                
                # Clean up the message by removing the leading dash and whitespace
                if message.startswith('-'):
                    message = message[1:].strip()

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": error_code,
                    "line": line_num,
                    "message": message,
                    "type": "error" if error_code.startswith("E") or error_code.startswith("F") else "warning"
                })

    elif tool_name == "darglint":
        # Extract file paths, line numbers, and error codes from darglint output
        for line in output.splitlines():
            # Match the darglint output format: "/path/to/file.py:function:123: I123: message"
            # Also handle the format without the method: "/path/to/file.py:123: I123: message"
            match = re.match(r"(.*?):([^:]+):(\d+): ([A-Z]+\d+): (.*)", line)
            if not match:
                # Try alternative format without method
                match = re.match(r"(.*?):(\d+): ([A-Z]+\d+): (.*)", line)
                if match:
                    file_path = match.group(1).strip()
                    rel_path = get_relative_path(file_path)
                    line_num = match.group(2)
                    error_code = match.group(3)
                    message = match.group(4).strip()
                    method_name = "N/A"
                    
                    # Clean up the message by removing the leading dash and whitespace
                    if message.startswith('-'):
                        message = message[1:].strip()

                    file_paths.append(rel_path)
                    line_numbers.append(line_num)
                    error_codes.append(error_code)

                    # Add to issues list for table formatting
                    issues.append({
                        "file": rel_path,
                        "code": error_code,
                        "line": line_num,
                        "method": method_name,
                        "message": message
                    })
            elif match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                method_name = match.group(2)
                line_num = match.group(3)
                error_code = match.group(4)
                message = match.group(5).strip()
                
                # Clean up the message by removing the leading dash and whitespace
                if message.startswith('-'):
                    message = message[1:].strip()

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": error_code,
                    "line": line_num,
                    "method": method_name,
                    "message": message
                })
            elif "Skipped" in line and "timeout" in line:
                # Handle skipped files due to timeout
                match = re.match(r"Skipped (.+) \(timeout", line)
                if match:
                    file_path = match.group(1)
                    rel_path = get_relative_path(file_path)
                    file_paths.append(rel_path)
                    line_numbers.append("N/A")
                    error_codes.append("TIMEOUT")

                    # Add to issues list for table formatting
                    issues.append({
                        "file": rel_path,
                        "code": "TIMEOUT",
                        "line": "N/A",
                        "method": "N/A",
                        "message": "Skipped due to timeout"
                    })

    elif tool_name == "hadolint":
        # Extract file paths, line numbers, and error codes from hadolint output
        for line in output.splitlines():
            # Match the hadolint output format: "/path/to/Dockerfile:123 DL3000 message"
            match = re.match(r"(.*?):(\d+) ([A-Z0-9]+) (.*)", line)
            if match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                line_num = match.group(2)
                error_code = match.group(3)
                message = match.group(4)

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": error_code,
                    "line": line_num,
                    "message": message
                })
            elif "No Dockerfile files found" in line:
                # Handle case where no Dockerfile files are found
                return "No Dockerfile files found in the specified paths."
            elif "Skipped" in line and "timeout" in line:
                # Handle skipped files due to timeout
                match = re.match(r"Skipped (.+) \(timeout", line)
                if match:
                    file_path = match.group(1)
                    rel_path = get_relative_path(file_path)
                    file_paths.append(rel_path)
                    line_numbers.append("N/A")
                    error_codes.append("TIMEOUT")

                    # Add to issues list for table formatting
                    issues.append({
                        "file": rel_path,
                        "code": "TIMEOUT",
                        "line": "N/A",
                        "message": "Skipped due to timeout"
                    })

    elif tool_name == "pydocstyle":
        # Extract file paths, line numbers, and error codes from pydocstyle output
        current_file = None
        current_line = None
        current_code = None

        for line in output.splitlines():
            # Match the file path line: "/path/to/file.py:123 at module level:"
            file_match = re.match(r"(.*?):(\d+)", line)
            # Match the error code line: "        D100: Missing docstring in public module"
            code_match = re.match(r"\s+([A-Z]\d+): (.*)", line)

            if file_match:
                current_file = file_match.group(1).strip()
                current_line = file_match.group(2)
            elif code_match and current_file:
                current_code = code_match.group(1)
                message = code_match.group(2)

                rel_path = get_relative_path(current_file)
                file_paths.append(rel_path)
                line_numbers.append(current_line)
                error_codes.append(current_code)

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": current_code,
                    "line": current_line,
                    "message": message
                })
            elif "Skipped" in line and "timeout" in line:
                # Handle skipped files due to timeout
                match = re.match(r"Skipped (.+) \(timeout", line)
                if match:
                    file_path = match.group(1)
                    rel_path = get_relative_path(file_path)
                    file_paths.append(rel_path)
                    line_numbers.append("N/A")
                    error_codes.append("TIMEOUT")

                    # Add to issues list for table formatting
                    issues.append({
                        "file": rel_path,
                        "code": "TIMEOUT",
                        "line": "N/A",
                        "message": "Skipped due to timeout"
                    })

    elif tool_name == "prettier":
        # Extract file paths from prettier output
        for line in output.splitlines():
            if line.endswith(" would be formatted"):
                file_path = line.replace(" would be formatted", "").strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("FORMAT")

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": "FORMAT",
                    "line": "N/A",
                    "message": "Formatting required"
                })
            elif "Prettier check timed out" in line:
                # Handle timeout
                return f"Prettier check timed out after {line.split(' ')[-2]} seconds."

    elif tool_name == "pylint":
        # Extract file paths, line numbers, and error codes from pylint output
        for line in output.splitlines():
            # Match the pylint output format: "sample.py:16:0: C0115: Missing class docstring (missing-class-docstring)"
            match = re.match(r"(.*?):(\d+):(\d+): ([A-Z]\d{4}): (.*) \((.*)\)", line)
            if match:
                file_path = match.group(1).strip()
                rel_path = get_relative_path(file_path)
                line_num = match.group(2)
                col_num = match.group(3)
                error_code = match.group(4)
                message = match.group(5).strip()
                error_name = match.group(6).strip()
                
                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": error_code,
                    "line": line_num,
                    "col": col_num,
                    "message": message,
                    "name": error_name,
                    "type": "error" if error_code.startswith("E") or error_code.startswith("F") else "warning"
                })
            # Skip summary lines
            elif "Your code has been rated at" in line or "---" in line or "Module" in line:
                continue
            # Try a simpler pattern for other pylint message formats
            elif ":" in line:
                match = re.search(r":(\d+):(\d+): ([A-Z]\d{4}):", line)
                if match:
                    parts = line.split(":", 5)
                    if len(parts) >= 5:
                        file_path = parts[0].strip()
                        rel_path = get_relative_path(file_path)
                        line_num = match.group(1)
                        col_num = match.group(2)
                        error_code = match.group(3)
                        
                        # Extract message and error name
                        message_parts = parts[4].strip().split(" (", 1)
                        message = message_parts[0].strip()
                        error_name = message_parts[1].rstrip(")") if len(message_parts) > 1 else ""
                        
                        file_paths.append(rel_path)
                        line_numbers.append(line_num)
                        error_codes.append(error_code)
                        
                        # Add to issues list for table formatting
                        issues.append({
                            "file": rel_path,
                            "code": error_code,
                            "line": line_num,
                            "col": col_num,
                            "message": message,
                            "name": error_name,
                            "type": "error" if error_code.startswith("E") or error_code.startswith("F") else "warning"
                        })

    elif tool_name == "semgrep":
        # Extract file paths, line numbers, and error codes from semgrep output
        current_file = None
        current_rule = None
        current_message = None
        current_line = None
        
        for line in output.splitlines():
            # Check if this is a file line (usually starts with spaces and the file path)
            file_match = re.match(r'\s+([^❯]+)$', line)
            if file_match:
                current_file = file_match.group(1).strip()
                continue
                
            # Check if this is a rule line (starts with ❯❯❱)
            rule_match = re.match(r'\s+❯❯❱\s+([^\s]+)', line)
            if rule_match:
                current_rule = rule_match.group(1).strip()
                continue
                
            # Check if this is a message line (usually indented with spaces)
            message_match = re.match(r'\s+([^❯][^┆]+)$', line)
            if message_match and current_file and current_rule:
                current_message = message_match.group(1).strip()
                continue
                
            # Check if this is a line number line (contains ┆)
            line_match = re.match(r'\s+(\d+)┆\s+(.*)', line)
            if line_match and current_file and current_rule and current_message:
                current_line = line_match.group(1)
                code_snippet = line_match.group(2).strip()
                
                # Get relative path
                rel_path = get_relative_path(current_file)
                
                # Add to lists for formatting
                file_paths.append(rel_path)
                line_numbers.append(current_line)
                error_codes.append(current_rule)
                
                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": current_rule,
                    "line": current_line,
                    "col": "0",  # Column information not easily available in new format
                    "severity": "ERROR",  # Severity not easily available in new format
                    "message": current_message,
                    "type": "error"
                })
                
                # Reset for next finding
                current_message = None
                current_line = None

    # Add terraform-specific parsing
    elif tool_name == "terraform":
        # Parse formatting issues
        if "Formatting issues found:" in output:
            # Extract the formatting diff
            fmt_section = re.search(r"Formatting issues found:\n(.*?)(?:\n\n|$)", output, re.DOTALL)
            if fmt_section:
                fmt_output = fmt_section.group(1)
                # Parse the diff to extract file paths and changes
                for line in fmt_output.splitlines():
                    if line.startswith("---") or line.startswith("+++"):
                        # Extract file path from diff header
                        file_match = re.search(r"[-+]{3} (?:a/|b/)?(.+)", line)
                        if file_match:
                            current_file = file_match.group(1)
                            rel_path = get_relative_path(current_file)
                            file_paths.append(rel_path)
                    elif line.startswith("-") or line.startswith("+"):
                        # Count as a formatting issue
                        issues.append({
                            "file": current_file if "current_file" in locals() else "Unknown",
                            "code": "FORMAT",
                            "line": "N/A",
                            "severity": "warning",
                            "message": "Formatting issue"
                        })
        
        # Parse validation issues
        if "Validation issues found:" in output:
            # Extract the validation section
            validate_section = re.search(r"Validation issues found:\n(.*?)(?:\n\n|$)", output, re.DOTALL)
            if validate_section:
                validate_output = validate_section.group(1)
                # Parse the validation output to extract errors
                for line in validate_output.splitlines():
                    # Look for directory and error information
                    dir_match = re.search(r"Directory (.+): \[(ERROR|WARNING)\] (.+)", line)
                    if dir_match:
                        dir_path = dir_match.group(1)
                        severity = dir_match.group(2).lower()
                        message = dir_match.group(3)
                        
                        issues.append({
                            "file": dir_path,
                            "code": "VALIDATE",
                            "line": "N/A",
                            "severity": severity,
                            "message": message
                        })

    # Add yamllint-specific parsing
    elif tool_name == "yamllint":
        # Parse yamllint output (format: file:line:column: [level] message)
        for line in output.splitlines():
            match = re.match(r"(.+):(\d+):(\d+): \[(error|warning)\] (.+)", line)
            if match:
                file_path, line_num, col_num, severity, message = match.groups()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(message.split(" ")[0])  # Use first word of message as code
                
                # Add to issues list for table formatting
                issues.append({
                    "file": rel_path,
                    "code": message.split(" ")[0],
                    "line": line_num,
                    "col": col_num,
                    "severity": severity,
                    "message": message
                })

    # If tabulate is available, table format is requested, and we have issues, format as a table
    if use_table_format and TABULATE_AVAILABLE and issues:
        return format_as_table(issues, tool_name, group_by)
    
    # If we have no issues but we're using table format, return the original output
    if use_table_format and not issues:
        return output

    # Calculate optimal column widths (min 10, max 60)
    path_width = max(min(max([len(p) for p in file_paths] or [10]), 60), 10)
    line_width = max(min(max([len(str(l)) for l in line_numbers] or [5]), 10), 5)
    code_width = max(min(max([len(c) for c in error_codes] or [10]), 20), 10)

    # Format each line with consistent spacing and colors
    for i, (path, line, code) in enumerate(zip(file_paths, line_numbers, error_codes)):
        if tool_name == "black":
            formatted_lines.append(
                click.style(f"- {path:<{path_width}}", fg="yellow")
                + click.style(f" : {'N/A':<{line_width}}", fg="blue")
                + click.style(f" : {'FORMAT':<{code_width}}", fg="red")
                + f" : formatting required"
            )
        elif tool_name == "isort":
            formatted_lines.append(
                click.style(f"- {path:<{path_width}}", fg="yellow")
                + click.style(f" : {'N/A':<{line_width}}", fg="blue")
                + click.style(f" : {'SORT':<{code_width}}", fg="red")
                + f" : import sorting required"
            )
        else:
            # Get the message for this issue
            message = ""
            for issue in issues:
                if (
                    issue.get("file") == path
                    and str(issue.get("line")) == str(line)
                    and issue.get("code") == code
                ):
                    message = issue.get("message", "")
                    break

            formatted_lines.append(
                click.style(f"- {path:<{path_width}}", fg="yellow")
                + click.style(f" : {line:<{line_width}}", fg="blue")
                + click.style(f" : {code:<{code_width}}", fg="red")
                + f" : {message}"
            )

    # Add a note about skipped files for isort
    if tool_name == "isort" and skipped_files > 0:
        formatted_lines.append(
            click.style(f"Note: Skipped {skipped_files} files", fg="blue")
        )

    # Join all lines with newlines
    if formatted_lines:
        return "\n".join(formatted_lines)
    else:
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
    help="Comma-separated list of tools to run (default: all tools that can check)",
)
@click.option(
    "--exclude",
    help="Comma-separated list of patterns to exclude (e.g., '*.pyc,venv')",
)
@click.option(
    "--include-venv",
    is_flag=True,
    help="Include virtual environment directories",
)
@click.option(
    "--output",
    "-o",
    help="Write output to a file",
)
@click.option(
    "--table-format",
    is_flag=True,
    help="Format output as a table",
)
@click.option(
    "--group-by",
    type=click.Choice(["file", "code", "none"]),
    default="file",
    help="Group issues by file, code, or none",
)
@click.option(
    "--ignore-conflicts",
    is_flag=True,
    help="Ignore tool conflicts",
)
@click.option(
    "--darglint-timeout",
    type=int,
    default=None,
    help="Timeout for darglint in seconds",
)
@click.option(
    "--hadolint-timeout",
    type=int,
    default=None,
    help="Timeout for hadolint in seconds",
)
@click.option(
    "--pydocstyle-timeout",
    type=int,
    default=None,
    help="Timeout for pydocstyle in seconds",
)
@click.option(
    "--pydocstyle-convention",
    type=str,
    default=None,
    help="Convention for pydocstyle (e.g., 'numpy', 'google')",
)
@click.option(
    "--prettier-timeout",
    type=int,
    default=None,
    help="Timeout for prettier in seconds",
)
@click.option(
    "--pylint-rcfile",
    type=str,
    default=None,
    help="Path to pylint configuration file",
)
@click.option(
    "--semgrep-config",
    type=str,
    default=None,
    help="Semgrep configuration option (default: auto)",
)
@click.option(
    "--terraform-recursive",
    is_flag=True,
    default=None,
    help="Recursively check Terraform directories",
)
@click.option(
    "--yamllint-config",
    type=str,
    default=None,
    help="Path to yamllint configuration file",
)
@click.option(
    "--yamllint-strict",
    is_flag=True,
    default=None,
    help="Use strict mode for yamllint",
)
@click.option(
    "--mypy-config",
    type=str,
    default=None,
    help="Path to mypy configuration file",
)
@click.option(
    "--mypy-python-version",
    type=str,
    default=None,
    help="Python version to use for mypy type checking",
)
@click.option(
    "--mypy-disallow-untyped-defs",
    is_flag=True,
    default=None,
    help="Disallow untyped function definitions in mypy",
)
@click.option(
    "--mypy-disallow-incomplete-defs",
    is_flag=True,
    default=None,
    help="Disallow incomplete function definitions in mypy",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show verbose output",
)
@click.option(
    "--debug-file",
    type=str,
    default=None,
    help="Write debug output to a file",
)
def check(
    paths: list[str],
    tools: str | None,
    exclude: str | None,
    include_venv: bool,
    output: str | None,
    table_format: bool,
    group_by: str,
    ignore_conflicts: bool,
    darglint_timeout: int | None,
    hadolint_timeout: int | None,
    pydocstyle_timeout: int | None,
    pydocstyle_convention: str | None,
    prettier_timeout: int | None,
    pylint_rcfile: str | None,
    semgrep_config: str | None,
    terraform_recursive: bool | None,
    yamllint_config: str | None,
    yamllint_strict: bool | None,
    mypy_config: str | None,
    mypy_python_version: str | None,
    mypy_disallow_untyped_defs: bool | None,
    mypy_disallow_incomplete_defs: bool | None,
    verbose: bool = False,
    debug_file: str | None = None,
):
    """Check files for issues without fixing them."""
    if not paths:
        paths = [os.getcwd()]

    # Open debug file if specified
    debug_file_handle = None
    if debug_file:
        try:
            debug_file_handle = open(debug_file, "w")
            debug_file_handle.write(f"Lintro check command\n")
            debug_file_handle.write(f"Paths: {paths}\n")
            debug_file_handle.write(f"Tools: {tools}\n")
        except IOError as e:
            click.echo(f"Error opening debug file: {e}", err=True)
            sys.exit(1)

    # Check if table format is requested but tabulate is not available
    if table_format and not TABULATE_AVAILABLE:
        click.echo(
            "Warning: Table formatting requested but tabulate package is not installed.",
            err=True,
        )
        click.echo("Install with: pip install tabulate", err=True)
        table_format = False

    # Parse tools list
    tool_list = parse_tool_list(tools) or list(CHECK_TOOLS.keys())

    # Resolve conflicts if needed
    if not ignore_conflicts:
        original_tool_count = len(tool_list)
        tool_list = get_tool_execution_order(tool_list)

        if len(tool_list) < original_tool_count:
            click.secho(
                f"Note: Some tools were excluded due to conflicts. Use --ignore-conflicts to run all tools.",
                fg="yellow",
            )

    tool_to_run = {
        name: tool
        for name, tool in CHECK_TOOLS.items()
        if not tool_list or name in tool_list
    }

    if not tool_to_run:
        click.echo(
            "No tools selected. Available tools: " + ", ".join(CHECK_TOOLS.keys())
        )
        if debug_file_handle:
            debug_file_handle.close()
        sys.exit(1)

    # Process exclude patterns
    exclude_patterns = []
    if exclude:
        exclude_patterns = [p.strip() for p in exclude.split(",") if p.strip()]

    # Open output file if specified
    output_file = None
    if output:
        try:
            output_file = open(output, "w")
            click.echo(f"Writing output to {output}")
        except IOError as e:
            click.echo(f"Error opening output file: {e}", err=True)
            if debug_file_handle:
                debug_file_handle.close()
            sys.exit(1)

    try:
        exit_code = 0
        results = []

        for name, tool in tool_to_run.items():
            if verbose:
                click.echo(f"Running tool: {name}")
            
            if debug_file_handle:
                debug_file_handle.write(f"\nRunning tool: {name}\n")
                
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(
                    exclude_patterns=exclude_patterns, include_venv=include_venv
                )

            # Set tool-specific options
            if name == "darglint" and darglint_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=darglint_timeout,
                )
            elif name == "hadolint" and hadolint_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=hadolint_timeout,
                )
            elif name == "pydocstyle":
                options = {}
                if pydocstyle_timeout is not None:
                    options["timeout"] = pydocstyle_timeout
                if pydocstyle_convention is not None:
                    options["convention"] = pydocstyle_convention
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )
            elif name == "prettier" and prettier_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=prettier_timeout,
                )
            elif name == "pylint" and pylint_rcfile is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    rcfile=pylint_rcfile,
                )
            elif name == "semgrep" and semgrep_config is not None:
                if verbose:
                    click.echo(f"Setting semgrep config to: {semgrep_config}")
                if debug_file_handle:
                    debug_file_handle.write(f"Setting semgrep config to: {semgrep_config}\n")
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    config_option=semgrep_config,
                )
            elif name == "terraform" and terraform_recursive is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    recursive=terraform_recursive,
                )
            elif name == "yamllint":
                options = {}
                if yamllint_config is not None:
                    options["config_file"] = yamllint_config
                if yamllint_strict is not None:
                    options["strict"] = yamllint_strict
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )
            elif name == "mypy":
                options = {}
                if mypy_config is not None:
                    options["config_file"] = mypy_config
                if mypy_python_version is not None:
                    options["python_version"] = mypy_python_version
                if mypy_disallow_untyped_defs is not None:
                    options["disallow_untyped_defs"] = mypy_disallow_untyped_defs
                if mypy_disallow_incomplete_defs is not None:
                    options["disallow_incomplete_defs"] = mypy_disallow_incomplete_defs
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )

            print_tool_header(name, "check", output_file, table_format)

            if verbose:
                click.echo(f"Running {name} on paths: {paths}")
            if debug_file_handle:
                debug_file_handle.write(f"Running {name} on paths: {paths}\n")
                
            success, output_text = tool.check(list(paths))

            if verbose:
                click.echo(f"Tool {name} returned success: {success}")
                click.echo(f"Output: {output_text}")
            if debug_file_handle:
                debug_file_handle.write(f"Tool {name} returned success: {success}\n")
                debug_file_handle.write(f"Output length: {len(output_text)}\n")
                debug_file_handle.write(f"Output: {output_text}\n")
                
            # Count issues and format output
            issues_count = count_issues(output_text, name)
            
            if verbose:
                click.echo(f"Issues count: {issues_count}")
            if debug_file_handle:
                debug_file_handle.write(f"Issues count: {issues_count}\n")
                
            formatted_output = format_tool_output(
                output_text, name, table_format, group_by
            )

            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                # Use the same formatted output for the file to ensure consistency
                click.echo(formatted_output, file=output_file)

            # Use issues_count to determine success
            # For tools that return success=True but have issues, override the success status
            if issues_count > 0:
                success = False

            print_tool_footer(success, issues_count, output_file, table_format, name)

            results.append(
                ToolResult(
                    name=name,
                    success=success,
                    output=output_text,
                    issues_count=issues_count,
                )
            )

            if not success:
                exit_code = 1

        print_summary(results, "check", output_file, table_format)

        if output_file:
            output_file.close()
        if debug_file_handle:
            debug_file_handle.close()

        sys.exit(exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if debug_file_handle:
            debug_file_handle.write(f"Error: {e}\n")
            debug_file_handle.close()
        if output_file:
            output_file.close()
        sys.exit(1)


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
@click.option(
    "--ignore-conflicts",
    is_flag=True,
    help="Ignore tool conflicts and run all specified tools",
)
@click.option(
    "--darglint-timeout",
    type=int,
    default=None,
    help="Timeout in seconds for darglint per file (default: 10)",
)
@click.option(
    "--hadolint-timeout",
    type=int,
    default=None,
    help="Timeout in seconds for hadolint per file (default: 10)",
)
@click.option(
    "--pydocstyle-timeout",
    type=int,
    default=None,
    help="Timeout in seconds for pydocstyle per file (default: 10)",
)
@click.option(
    "--pydocstyle-convention",
    type=click.Choice(["pep257", "numpy", "google"]),
    default=None,
    help="Docstring style convention for pydocstyle (default: pep257)",
)
@click.option(
    "--prettier-timeout",
    type=int,
    default=None,
    help="Timeout in seconds for prettier (default: 30)",
)
@click.option(
    "--pylint-rcfile",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to pylint configuration file",
)
@click.option(
    "--semgrep-config",
    type=str,
    default=None,
    help="Semgrep configuration option (default: auto)",
)
@click.option(
    "--terraform-recursive",
    is_flag=True,
    default=None,
    help="Recursively format Terraform directories",
)
@click.option(
    "--yamllint-config",
    type=str,
    default=None,
    help="Path to yamllint configuration file",
)
@click.option(
    "--yamllint-strict",
    is_flag=True,
    default=None,
    help="Use strict mode for yamllint",
)
@click.option(
    "--mypy-config",
    type=str,
    default=None,
    help="Path to mypy configuration file",
)
@click.option(
    "--mypy-python-version",
    type=str,
    default=None,
    help="Python version to use for mypy type checking",
)
@click.option(
    "--mypy-disallow-untyped-defs",
    is_flag=True,
    default=None,
    help="Disallow untyped function definitions in mypy",
)
@click.option(
    "--mypy-disallow-incomplete-defs",
    is_flag=True,
    default=None,
    help="Disallow incomplete function definitions in mypy",
)
def fmt(
    paths: list[str],
    tools: str | None,
    exclude: str | None,
    include_venv: bool,
    output: str | None,
    table_format: bool,
    group_by: str,
    ignore_conflicts: bool,
    darglint_timeout: int | None,
    hadolint_timeout: int | None,
    pydocstyle_timeout: int | None,
    pydocstyle_convention: str | None,
    prettier_timeout: int | None,
    pylint_rcfile: str | None,
    semgrep_config: str | None,
    terraform_recursive: bool | None,
    yamllint_config: str | None,
    yamllint_strict: bool | None,
    mypy_config: str | None,
    mypy_python_version: str | None,
    mypy_disallow_untyped_defs: bool | None,
    mypy_disallow_incomplete_defs: bool | None,
):
    """Format files to fix issues."""
    if not paths:
        paths = [os.getcwd()]

    # Check if table format is requested but tabulate is not available
    if table_format and not TABULATE_AVAILABLE:
        click.echo(
            "Warning: Table formatting requested but tabulate package is not installed.",
            err=True,
        )
        click.echo("Install with: pip install tabulate", err=True)
        table_format = False

    # Parse tools list
    tool_list = parse_tool_list(tools) or list(FIX_TOOLS.keys())

    # Resolve conflicts if needed
    if not ignore_conflicts:
        original_tool_count = len(tool_list)
        tool_list = get_tool_execution_order(tool_list)

        if len(tool_list) < original_tool_count:
            click.secho(
                f"Note: Some tools were excluded due to conflicts. Use --ignore-conflicts to run all tools.",
                fg="yellow",
            )

    tool_to_run = {
        name: tool
        for name, tool in FIX_TOOLS.items()
        if not tool_list or name in tool_list
    }

    if not tool_to_run:
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
            output_file = open(output, "w")
            click.echo(f"Writing output to {output}")
        except IOError as e:
            click.echo(f"Error opening output file: {e}", err=True)
            sys.exit(1)

    try:
        exit_code = 0
        results = []

        for name, tool in tool_to_run.items():
            # Modify tool command based on options
            if hasattr(tool, "set_options"):
                tool.set_options(
                    exclude_patterns=exclude_patterns, include_venv=include_venv
                )

            # Set tool-specific options
            if name == "darglint" and darglint_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=darglint_timeout,
                )
            elif name == "hadolint" and hadolint_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=hadolint_timeout,
                )
            elif name == "pydocstyle":
                options = {}
                if pydocstyle_timeout is not None:
                    options["timeout"] = pydocstyle_timeout
                if pydocstyle_convention is not None:
                    options["convention"] = pydocstyle_convention
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )
            elif name == "prettier" and prettier_timeout is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    timeout=prettier_timeout,
                )
            elif name == "pylint" and pylint_rcfile is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    rcfile=pylint_rcfile,
                )
            elif name == "semgrep" and semgrep_config is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    config_option=semgrep_config,
                )
            elif name == "terraform" and terraform_recursive is not None:
                tool.set_options(
                    exclude_patterns=exclude_patterns,
                    include_venv=include_venv,
                    recursive=terraform_recursive,
                )
            elif name == "yamllint":
                options = {}
                if yamllint_config is not None:
                    options["config_file"] = yamllint_config
                if yamllint_strict is not None:
                    options["strict"] = yamllint_strict
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )
            elif name == "mypy":
                options = {}
                if mypy_config is not None:
                    options["config_file"] = mypy_config
                if mypy_python_version is not None:
                    options["python_version"] = mypy_python_version
                if mypy_disallow_untyped_defs is not None:
                    options["disallow_untyped_defs"] = mypy_disallow_untyped_defs
                if mypy_disallow_incomplete_defs is not None:
                    options["disallow_incomplete_defs"] = mypy_disallow_incomplete_defs
                
                if options:
                    tool.set_options(
                        exclude_patterns=exclude_patterns,
                        include_venv=include_venv,
                        **options,
                    )

            print_tool_header(name, "format", output_file, table_format)

            success, output_text = tool.fix(list(paths))

            # Count issues and format output
            issues_count = count_issues(output_text, name)
            formatted_output = format_tool_output(
                output_text, name, table_format, group_by
            )

            # Always display in console, and also in file if specified
            click.echo(formatted_output)
            if output_file:
                # Use the same formatted output for the file to ensure consistency
                click.echo(formatted_output, file=output_file)

            # Use issues_count to determine success
            # For tools that return success=True but have issues, override the success status
            if issues_count > 0:
                success = False
                
            print_tool_footer(success, issues_count, output_file, table_format, name)

            results.append(
                ToolResult(
                    name=name,
                    success=success,
                    output=output_text,
                    issues_count=issues_count,
                )
            )

            if not success:
                exit_code = 1

        print_summary(results, "format", output_file, table_format)

        if output_file:
            output_file.close()

        sys.exit(exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if output_file:
            output_file.close()
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file to write results to",
)
@click.option(
    "--show-conflicts",
    is_flag=True,
    help="Show potential conflicts between tools",
)
def list_tools(output: str | None, show_conflicts: bool):
    """List all available tools."""
    # Open output file if specified
    output_file = None
    if output:
        try:
            output_file = open(output, "w")
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
                click.secho(
                    "\nTools that can fix issues:", fg="green", file=output_file
                )
                for name, tool in fix_tools:
                    click.echo(f"  - {name}: {tool.description}", file=output_file)

        if check_only_tools:
            # Display in console
            click.secho("\nTools that can only check for issues:", fg="yellow")
            for name, tool in check_only_tools:
                click.echo(f"  - {name}: {tool.description}")

            # Also write to file if specified
            if output_file:
                click.secho(
                    "\nTools that can only check for issues:",
                    fg="yellow",
                    file=output_file,
                )
                for name, tool in check_only_tools:
                    click.echo(f"  - {name}: {tool.description}", file=output_file)

        # Add conflict information if requested
        if show_conflicts:
            click.secho("\nPotential Tool Conflicts:", fg="yellow")

            # Check each tool for conflicts
            for name, tool in AVAILABLE_TOOLS.items():
                if tool.config.conflicts_with:
                    conflicts = [
                        c for c in tool.config.conflicts_with if c in AVAILABLE_TOOLS
                    ]
                    if conflicts:
                        click.secho(f"  {name}:", fg="yellow")
                        for conflict in conflicts:
                            click.secho(
                                f"    - {conflict} (priority: {AVAILABLE_TOOLS[conflict].config.priority})",
                                fg="yellow",
                            )
                        click.secho(
                            f"  {name} priority: {tool.config.priority}", fg="yellow"
                        )
                        click.secho("")
    finally:
        # Close the output file if it was opened
        if output_file:
            output_file.close()


def main():
    """Entry point for the CLI."""
    cli()
