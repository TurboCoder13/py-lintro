"""Command-line interface for Lintro."""

import os
import re
import sys
from dataclasses import dataclass
from typing import TextIO

import click

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
        return len(re.findall(r":\d+:\d+: [A-Z]+\d{3}", output))
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
    else:
        # Generic fallback: count lines that look like issues
        return len(re.findall(r"(error|warning|issue|problem)", output, re.IGNORECASE))


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
        file: File to write output to
        use_table_format: Whether to use table formatting
    """
    if not use_table_format:
        # Standard format
        click.secho("\n" + "=" * 60, fg="blue")
        click.secho(f" Running {tool_name} ({action})", fg="blue", bold=True)
        click.secho("=" * 60, fg="blue")

        # Also write to file if specified
        if file:
            click.secho("\n" + "=" * 60, fg="blue", file=file)
            click.secho(
                f" Running {tool_name} ({action})", fg="blue", bold=True, file=file
            )
            click.secho("=" * 60, fg="blue", file=file)
    else:
        # Table format
        header = "\n" + "-" * 60 + f"\n Running {tool_name} ({action})\n" + "-" * 60
        click.secho(header, fg="blue", bold=True)
        if file:
            click.secho(header, fg="blue", bold=True, file=file)


def print_tool_footer(
    success: bool,
    issues_count: int,
    file: TextIO | None = None,
    use_table_format: bool = False,
):
    """
    Print a footer for a tool's output.

    Args:
        success: Whether the tool ran successfully
        issues_count: Number of issues found
        file: File to write output to
        use_table_format: Whether to use table formatting
    """
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
    """
    Print a summary of all tool results.

    Args:
        results: List of tool results
        action: Action that was performed (check or fix)
        file: File to write output to
        use_table_format: Whether to use table formatting
    """
    total_issues = sum(result.issues_count for result in results)

    if not use_table_format:
        # Standard format
        click.secho("\n" + "=" * 60, fg="blue")
        click.secho(" Summary (" + action + ")", fg="blue", bold=True)
        click.secho("=" * 60, fg="blue")

        for result in results:
            if result.issues_count == 0:
                click.secho(f" ✓ {result.name}: No issues", fg="green")
            else:
                click.secho(f" ✗ {result.name}: {result.issues_count} issues", fg="red")

        click.secho("-" * 60, fg="blue")

        if total_issues == 0:
            click.secho(" Total: No issues found", fg="green")
        else:
            click.secho(f" Total: {total_issues} issues found", fg="red")

        click.secho("=" * 60, fg="blue")

        # Also write to file if specified
        if file:
            click.secho("\n" + "=" * 60, fg="blue", file=file)
            click.secho(" Summary (" + action + ")", fg="blue", bold=True, file=file)
            click.secho("=" * 60, fg="blue", file=file)

            for result in results:
                if result.issues_count == 0:
                    click.secho(f" ✓ {result.name}: No issues", fg="green", file=file)
                else:
                    click.secho(
                        f" ✗ {result.name}: {result.issues_count} issues",
                        fg="red",
                        file=file,
                    )

            click.secho("-" * 60, fg="blue", file=file)

            if total_issues == 0:
                click.secho(" Total: No issues found", fg="green", file=file)
            else:
                click.secho(f" Total: {total_issues} issues found", fg="red", file=file)

            click.secho("=" * 60, fg="blue", file=file)
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
            message = (
                "No issues"
                if result.issues_count == 0
                else f"{result.issues_count} issues"
            )

            summary_data.append(
                [
                    click.style(status, fg=status_color),
                    result.name,
                    click.style(message, fg=status_color),
                ]
            )

        summary_table = tabulate(
            summary_data,
            headers=["Status", "Tool", "Result"],
            tablefmt="pretty",
            colalign=("left", "left", "left"),  # Left align all columns
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


def format_as_table(
    issues: list[dict],
    tool_name: str | None = None,
    group_by: str = "file",
) -> str:
    """
    Format issues as a table.

    Args:
        issues: List of issues to format
        tool_name: Name of the tool that generated the issues
        group_by: How to group the issues (file, code, none, or auto)

    Returns:
        Formatted table as a string
    """
    if not issues:
        return ""

    result = []

    # Determine appropriate grouping
    if group_by == "auto":
        # For flake8, group by code
        if tool_name == "flake8":
            group_by = "code"
        else:
            group_by = "file"

    # Format based on tool and grouping
    if tool_name == "flake8":
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
                    table_data.append([issue["line"], issue["code"], issue["message"]])

                # Format as a table with headers - use left alignment
                headers = ["Line", "PEP Code", "Message"]

                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left"),
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
                    table_data.append([issue["path"], issue["line"], issue["message"]])

                # Format as a table with headers - use left alignment
                headers = ["File", "Line", "Message"]

                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left"),
                )

                result.append(table)

        else:  # No grouping
            # Convert issues to a list of lists for tabulate
            table_data = []
            for issue in issues:
                table_data.append(
                    [issue["path"], issue["line"], issue["code"], issue["message"]])

            # Format as a table with headers - use left alignment
            headers = ["File", "Line", "PEP Code", "Message"]

            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left", "left", "left", "left"),
            )

            result.append(table)

    else:
        # Generic format for other tools (darglint, hadolint, etc.)
        if group_by == "file":
            # Group by file
            issues_by_file = {}
            for issue in issues:
                path = issue["path"]
                if path not in issues_by_file:
                    issues_by_file[path] = []
                issues_by_file[path].append(issue)

            for file_path, file_issues in sorted(issues_by_file.items()):
                # Add file header
                result.append(f"\nFile: {file_path}")

                # Convert issues to a list of lists for tabulate
                table_data = []
                for issue in file_issues:
                    table_data.append([issue["line"], issue["code"], issue["message"]])

                # Format as a table with headers - use left alignment
                headers = ["Line", "Code", "Message"]

                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left"),
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
                    table_data.append([issue["path"], issue["line"], issue["message"]])

                # Format as a table with headers - use left alignment
                headers = ["File", "Line", "Message"]

                table = tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="pretty",
                    colalign=("left", "left", "left"),
                )

                result.append(table)

        else:  # No grouping
            # Convert issues to a list of lists for tabulate
            table_data = []
            for issue in issues:
                table_data.append(
                    [issue["path"], issue["line"], issue["code"], issue["message"]])

            # Format as a table with headers - use left alignment
            headers = ["File", "Line", "Code", "Message"]

            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pretty",
                colalign=("left", "left", "left", "left"),
            )

            result.append(table)

    return "\n".join(result)


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
        output.strip() == "All files are formatted correctly."):
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
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = line.replace("would reformat ", "").strip()
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("FORMAT")

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": "N/A",
                        "code": "FORMAT",
                        "message": "formatting required",
                    }
                )

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
                error_codes.append("ISORT")

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": "N/A",
                        "code": "ISORT",
                        "message": "import sorting required",
                    }
                )
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
                issues.append(
                    {
                        "path": rel_path,
                        "line": line_num,
                        "code": error_code,
                        "message": message,
                    }
                )

    elif tool_name == "darglint":
        # Extract and format darglint errors
        for line in output.splitlines():
            # Match darglint output format: file:method:line: code message
            # Example: /path/to/file.py:method_name:10: DAR101 Missing parameter(s) in Docstring: ['param']
            match = re.match(r"(.+):([^:]+):(\d+): ([A-Z]+\d{3}) (.+)", line)
            if match:
                file_path = match.group(1)
                method_name = match.group(2)
                line_num = match.group(3)
                error_code = match.group(4)
                message = match.group(5)
                rel_path = get_relative_path(file_path)

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": line_num,
                        "code": error_code,
                        "message": f"{message} (in method {method_name})",
                    }
                )
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
                    issues.append(
                        {
                            "path": rel_path,
                            "line": "N/A",
                            "code": "TIMEOUT",
                            "message": "skipped due to timeout",
                        }
                    )

    elif tool_name == "hadolint":
        # Extract and format hadolint errors
        for line in output.splitlines():
            # Match hadolint output format: file:line DL/SC code message
            match = re.match(r"(.+):(\d+) ((?:DL|SC)\d{4}) (.+)", line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                error_code = match.group(3)
                message = match.group(4)
                rel_path = get_relative_path(file_path)

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": line_num,
                        "code": error_code,
                        "message": message,
                    }
                )
            elif "No Dockerfile files found" in line:
                # Handle case where no Dockerfile files are found
                return "No Dockerfile files found in the specified paths."

    elif tool_name == "pydocstyle":
        # Extract and format pydocstyle errors
        for line in output.splitlines():
            # Match pydocstyle output format: file:line [code] message
            match = re.match(r"(.+):(\d+).*?([D]\d{3})(.*)", line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                error_code = match.group(3)
                message = match.group(4).strip()
                rel_path = get_relative_path(file_path)

                file_paths.append(rel_path)
                line_numbers.append(line_num)
                error_codes.append(error_code)

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": line_num,
                        "code": error_code,
                        "message": message,
                    }
                )
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
                    issues.append(
                        {
                            "path": rel_path,
                            "line": "N/A",
                            "code": "TIMEOUT",
                            "message": "skipped due to timeout",
                        }
                    )

    elif tool_name == "prettier":
        # Extract and format prettier errors
        for line in output.splitlines():
            # Match prettier output format: [warn] file would be formatted
            match = re.match(r"\[warn\] (.+) would be formatted", line)
            if match:
                file_path = match.group(1)
                rel_path = get_relative_path(file_path)
                file_paths.append(rel_path)
                line_numbers.append("N/A")
                error_codes.append("FORMAT")

                # Add to issues list for table formatting
                issues.append(
                    {
                        "path": rel_path,
                        "line": "N/A",
                        "code": "FORMAT",
                        "message": "formatting required",
                    }
                )

    # If tabulate is available, table format is requested, and we have issues, format as a table
    if TABULATE_AVAILABLE and use_table_format and issues:
        table = format_as_table(issues, tool_name, group_by)
        if table:
            # Add any summary lines
            if tool_name == "black":
                for line in output.splitlines():
                    if (
                        "All done!" in line
                        or "Oh no!" in line
                        or "files would be" in line
                    ):
                        if "All done!" in line:
                            table += "\n" + click.style(line, fg="green")
                        else:
                            table += "\n" + click.style(line, fg="red")

            # Add any skipped files notes for isort
            if tool_name == "isort" and skipped_files > 0:
                table += "\n" + click.style(
                    f"Note: Skipped {skipped_files} files", fg="blue"
                )

            # Add any skipped files notes for darglint
            if tool_name == "darglint" and "Skipped" in output and "files due to timeout" in output:
                match = re.search(r"Skipped (\d+) files due to timeout", output)
                if match:
                    skipped_count = match.group(1)
                    table += "\n" + click.style(
                        f"Note: Skipped {skipped_count} files due to timeout", fg="blue"
                    )

            # Add any skipped files notes for hadolint
            if tool_name == "hadolint" and "Skipped" in output and "files due to timeout" in output:
                match = re.search(r"Skipped (\d+) files due to timeout", output)
                if match:
                    skipped_count = match.group(1)
                    table += "\n" + click.style(
                        f"Note: Skipped {skipped_count} files due to timeout", fg="blue"
                    )

            # Add any skipped files notes for pydocstyle
            if tool_name == "pydocstyle" and "Skipped" in output and "files due to timeout" in output:
                match = re.search(r"Skipped (\d+) files due to timeout", output)
                if match:
                    skipped_count = match.group(1)
                    table += "\n" + click.style(
                        f"Note: Skipped {skipped_count} files due to timeout", fg="blue"
                    )

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
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {'N/A':<{line_width}}", fg="blue")
                    + click.style(f" : {'FORMAT':<{code_width}}", fg="red")
                    + f" : formatting required"
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
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {'N/A':<{line_width}}", fg="blue")
                    + click.style(f" : {'ISORT':<{code_width}}", fg="red")
                    + f" : import sorting required"
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
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {line_num:<{line_width}}", fg="blue")
                    + click.style(f" : {error_code:<{code_width}}", fg="red")
                    + f" : {message}"
                )
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)

    elif tool_name == "darglint":
        # Format darglint errors
        for line in output.splitlines():
            # Match darglint output format: file:method:line: code message
            match = re.match(r"(.+):([^:]+):(\d+): ([A-Z]+\d{3}) (.+)", line)
            if match:
                file_path = match.group(1)
                method_name = match.group(2)
                line_num = match.group(3)
                error_code = match.group(4)
                message = match.group(5)
                rel_path = get_relative_path(file_path)

                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {line_num:<{line_width}}", fg="blue")
                    + click.style(f" : {error_code:<{code_width}}", fg="red")
                    + f" : {message} (in method {method_name})"
                )
            elif "Skipped" in line:
                # Handle skipped files due to timeout
                formatted_lines.append(click.style(line, fg="blue"))
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)

    elif tool_name == "hadolint":
        # Format hadolint errors
        for line in output.splitlines():
            # Match hadolint output format: file:line DL/SC code message
            match = re.match(r"(.+):(\d+) ((?:DL|SC)\d{4}) (.+)", line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                error_code = match.group(3)
                message = match.group(4)
                rel_path = get_relative_path(file_path)

                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {line_num:<{line_width}}", fg="blue")
                    + click.style(f" : {error_code:<{code_width}}", fg="red")
                    + f" : {message}"
                )
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)

    elif tool_name == "pydocstyle":
        # Format pydocstyle errors
        for line in output.splitlines():
            # Match pydocstyle output format: file:line [code] message
            match = re.match(r"(.+):(\d+).*?([D]\d{3})(.*)", line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                error_code = match.group(3)
                message = match.group(4).strip()
                rel_path = get_relative_path(file_path)

                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {line_num:<{line_width}}", fg="blue")
                    + click.style(f" : {error_code:<{code_width}}", fg="red")
                    + f" : {message}"
                )
            elif "Skipped" in line:
                # Handle skipped files due to timeout
                formatted_lines.append(click.style(line, fg="blue"))
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)

    elif tool_name == "prettier":
        # Format prettier errors
        for line in output.splitlines():
            # Match prettier output format: [warn] file would be formatted
            match = re.match(r"\[warn\] (.+) would be formatted", line)
            if match:
                file_path = match.group(1)
                rel_path = get_relative_path(file_path)

                # Convert to standardized format with color and dynamic alignment
                formatted_lines.append(
                    click.style(f"- {rel_path:<{path_width}}", fg="yellow")
                    + click.style(f" : {'N/A':<{line_width}}", fg="blue")
                    + click.style(f" : {'FORMAT':<{code_width}}", fg="red")
                    + f" : formatting required"
                )
            elif line.strip() and not line.startswith("---"):
                # Keep other non-empty, non-separator lines
                formatted_lines.append(line)

    else:
        # For other tools, just return the original output
        return output

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
):
    """Check files for issues without fixing them."""
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

            print_tool_header(name, "check", output_file, table_format)

            success, output_text = tool.check(list(paths))

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

            print_tool_footer(success, issues_count, output_file, table_format)

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

        sys.exit(exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
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

            print_tool_header(name, "fix", output_file, table_format)

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
                
            print_tool_footer(success, issues_count, output_file, table_format)

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
