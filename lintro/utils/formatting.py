"""Formatting utilities for core output."""

from pathlib import Path
from typing import TextIO

import click
from tabulate import tabulate

from lintro.models.core.tool_result import ToolResult


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a core.

    Args:
        tool_name: Name of the core.

    Returns:
        Emoji for the core.
    """
    emojis = {
        "darglint": "📝",
        "hadolint": "🐳",
        "prettier": "💅",
        "ruff": "🦀",
        "yamllint": "📄",
    }
    return emojis.get(tool_name, "🔧")


def print_tool_header(
    tool_name: str,
    action: str,
    file: TextIO | None = None,
    output_format: str = "grid",
) -> None:
    """Print a header for a core in the old decorative style.

    Args:
        tool_name: Name of the core.
        action: Action being performed.
        file: File to write to (default: stdout).
        output_format: Output format being used.
    """
    # Skip headers for JSON format to keep output clean
    if output_format == "json":
        return

    # Old style: decorative borders with emojis
    border = "=" * 70
    emoji = get_tool_emoji(tool_name)
    emojis = f"{emoji} {emoji} {emoji} {emoji} {emoji}"
    header = f"{border}\n✨  Running {tool_name} ({action})    {emojis}\n{border}\n"
    click.echo(header, file=file)


def print_tool_footer(
    success: bool,
    issues_count: int,
    file: TextIO | None = None,
    output_format: str = "grid",
    tool_name: str = "",
    tool_output: str = "",
    action: str = "check",
) -> None:
    """Print a footer for a core in the old style.

    Args:
        success: Whether the core succeeded.
        issues_count: Number of issues found.
        file: File to write to (default: stdout).
        output_format: Output format being used.
        tool_name: Name of the core (for styling).
        tool_output: Raw output from the tool to check for duplicate messages.
        action: The action being performed (check, fmt, etc.).
    """
    # Skip footers for JSON format to keep output clean
    if output_format == "json":
        return

    # Handle different scenarios based on action and results
    if success and issues_count == 0:
        message = "No issues found."
        styled_message = click.style(f"✓ {message}", fg="green", bold=True)
    elif not success and issues_count > 0:
        if action == "fmt":
            # For format operations, issues remaining means they couldn't be auto-fixed
            styled_message = click.style(
                f"✗ Found {issues_count} issues that cannot be auto-fixed",
                fg="red",
                bold=True,
            )
        else:
            # For check operations, standard message
            styled_message = click.style(
                f"✗ Found {issues_count} issues", fg="red", bold=True
            )
    elif success and issues_count > 0:
        # Partial success - some issues were fixed but others remain
        if action == "fmt":
            styled_message = click.style(
                f"⚠ {issues_count} issues remain unfixed", fg="yellow", bold=True
            )
        else:
            styled_message = click.style(
                f"✗ Found {issues_count} issues", fg="red", bold=True
            )
    else:
        # Fallback
        styled_message = click.style("✗ Tool execution failed", fg="red", bold=True)

    click.echo(styled_message, file=file)
    click.echo()  # Add blank line after each tool


def read_ascii_art(filename: str) -> list[str]:
    """Read ASCII art from a file.

    Args:
        filename: Name of the ASCII art file.

    Returns:
        List of lines from one randomly selected ASCII art section.
    """
    import random

    try:
        # Get the path to the ASCII art file
        ascii_art_dir = Path(__file__).parent.parent / "ascii-art"
        file_path = ascii_art_dir / filename

        # Read the file and parse sections
        with file_path.open("r", encoding="utf-8") as f:
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
    except (FileNotFoundError, OSError):
        # Return empty list if file not found or can't be read
        return []


def print_summary(
    results: list[ToolResult],
    action: str,
    file: TextIO | None = None,
    output_format: str = "grid",
) -> None:
    """Print a summary of all core results in the old style.

    Args:
        results: List of ToolResult objects.
        action: Action performed (check, fix, etc.).
        file: File to write to (default: stdout).
        output_format: Output format being used.
    """
    if not results:
        return

    # For JSON format, create a consolidated JSON structure
    if output_format == "json":
        import json
        from datetime import datetime

        # Parse individual tool results from JSON strings
        tools_data = {}
        total_issues = 0

        for result in results:
            if hasattr(result, "formatted_output") and result.formatted_output:
                try:
                    # Parse the JSON output from the tool
                    tool_json = json.loads(result.formatted_output)

                    # Extract tool data if it's in the new format
                    if (
                        "lintro_results" in tool_json
                        and "tools" in tool_json["lintro_results"]
                    ):
                        tools_data.update(tool_json["lintro_results"]["tools"])
                        total_issues += tool_json["lintro_results"]["summary"][
                            "total_issues"
                        ]
                    else:
                        # Fallback for old format - use tool name from result
                        tool_name = result.name
                        tools_data[tool_name] = tool_json
                        total_issues += tool_json.get("summary", {}).get(
                            "total_issues", 0
                        )

                except (json.JSONDecodeError, KeyError):
                    # If we can't parse the JSON, create a basic structure
                    tools_data[result.name] = {
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "format_version": "1.0",
                        },
                        "summary": {
                            "total_issues": result.issues_count,
                            "has_issues": result.issues_count > 0,
                        },
                        "issues": [],
                    }
                    total_issues += result.issues_count

        # Create consolidated output
        consolidated_output = {
            "lintro_results": {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "format_version": "1.0",
                    "format": "json",
                    "action": action,
                },
                "summary": {
                    "total_tools": len(results),
                    "total_issues": total_issues,
                    "has_issues": total_issues > 0,
                    "successful_tools": sum(
                        1 for result in results if result.issues_count == 0
                    ),
                },
                "tools": tools_data,
            }
        }

        # Output only JSON, no other messages
        json_output = json.dumps(consolidated_output, indent=2, sort_keys=True)
        click.echo(json_output, file=file)
        return

    # For other structured formats, concatenate the formatted outputs
    elif output_format in ["markdown", "html", "csv"]:
        # Write individual tool results first
        for result in results:
            if hasattr(result, "formatted_output") and result.formatted_output:
                click.echo(result.formatted_output, file=file)
                if file:
                    click.echo("\n", file=file)  # Add spacing between tools

        # Then write the summary
        pass  # Let it fall through to the summary logic below

    # Calculate totals for non-JSON formats
    total_issues = sum(result.issues_count for result in results)

    # Show modern summary table for console formats
    if output_format in ["grid", "plain"]:
        # Create modern summary table with better styling
        summary_data = []
        for result in results:
            # Tool name with emoji (first column)
            tool_emoji = get_tool_emoji(result.name)
            tool_display = f"{tool_emoji} {result.name}"

            # Status with just emoji (no duplicate icon)
            if result.issues_count == 0:
                status_display = click.style("✅ PASS", fg="green", bold=True)
            else:
                status_display = click.style("❌ FAIL", fg="red", bold=True)

            # Issues count with color coding
            if result.issues_count == 0:
                issues_display = click.style(
                    str(result.issues_count), fg="green", bold=True
                )
            elif result.issues_count <= 5:
                issues_display = click.style(
                    str(result.issues_count), fg="yellow", bold=True
                )
            else:
                issues_display = click.style(
                    str(result.issues_count), fg="red", bold=True
                )

            summary_data.append([tool_display, status_display, issues_display])

        # Print modern summary table
        click.echo()  # Add spacing before table
        click.echo(click.style("📋 EXECUTION SUMMARY", fg="cyan", bold=True))
        click.echo(click.style("=" * 50, fg="cyan"))

        headers = [
            click.style("Tool", fg="cyan", bold=True),
            click.style("Status", fg="cyan", bold=True),
            click.style("Issues", fg="cyan", bold=True),
        ]

        # Use simple grid format for better alignment
        table = tabulate(
            summary_data, headers=headers, tablefmt="grid", stralign="left"
        )
        click.echo(table, file=file)

        # Add detached totals section
        click.echo()
        if total_issues == 0:
            click.echo(
                click.style(
                    "🎉 ALL TOOLS PASSED - NO ISSUES FOUND", fg="green", bold=True
                )
            )
        else:
            click.echo(
                click.style(f"⚠️  TOTAL ISSUES: {total_issues}", fg="red", bold=True)
            )

        click.echo()  # Add spacing

    # Old style: ASCII art
    if total_issues == 0:
        # Success case
        ascii_art = read_ascii_art("success.txt")
        if ascii_art:
            click.echo("\n".join(ascii_art), file=file)
    else:
        # Failure case
        ascii_art = read_ascii_art("fail.txt")
        if ascii_art:
            click.echo("\n".join(ascii_art), file=file)

    # Output to console and file if specified
    if file:
        click.echo("", file=file)  # Add final newline
