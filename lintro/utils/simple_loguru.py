"""Simplified Loguru-based logging utility for Lintro.

Single responsibility: Handle console display and file logging using Loguru.
No tee, no stream redirection, clean and simple with rich formatting.
"""

import sys
from pathlib import Path
from typing import Any
import click
from loguru import logger
from lintro.utils.formatting import read_ascii_art


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a tool.

    Args:
        tool_name: Name of the tool.

    Returns:
        Emoji for the tool.
    """
    emojis = {
        "ruff": "🦀",
        "prettier": "💅",
        "darglint": "📝",
        "hadolint": "🐳",
        "yamllint": "📄",
    }
    return emojis.get(tool_name, "🔧")


class SimpleLintroLogger:
    """Simple Loguru-based logger for Lintro commands with rich formatting."""

    def __init__(self, run_dir: Path, verbose: bool = False):
        """Initialize logger for a specific run.

        Args:
            run_dir: Directory to write log files to
            verbose: Whether to show debug messages on console
        """
        self.run_dir = run_dir
        self.verbose = verbose
        self.console_messages: list[str] = []  # Track console output for console.log

        # Configure Loguru
        self._setup_loguru()

    def _setup_loguru(self) -> None:
        """Configure Loguru with clean, simple handlers."""
        # Remove default handler
        logger.remove()

        # Add console handler (for immediate display)
        console_level = "DEBUG" if self.verbose else "INFO"
        logger.add(
            sys.stderr,
            level=console_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            colorize=True,
        )

        # Add debug.log handler (captures everything)
        debug_log_path = self.run_dir / "debug.log"
        logger.add(
            debug_log_path,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=None,  # Don't rotate, each run gets its own file
        )

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message and track for console.log."""
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message and track for console.log."""
        self.console_messages.append(f"WARNING: {message}")
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message and track for console.log."""
        self.console_messages.append(f"ERROR: {message}")
        logger.error(message, **kwargs)

    def console_output(self, text: str, color: str | None = None) -> None:
        """Display text on console and track for console.log.

        Args:
            text: Text to display
            color: Optional color for the text
        """
        if color:
            click.echo(click.style(text, fg=color))
        else:
            click.echo(text)

        # Track for console.log (without color codes)
        self.console_messages.append(text)

    def success(self, message: str) -> None:
        """Print a success message to console and log it."""
        self.console_output(message, color="green")
        logger.debug(f"SUCCESS: {message}")

    def print_lintro_header(
        self, action: str, tools_count: int, tools_list: str
    ) -> None:
        """Print the main Lintro header with run information."""
        header_msg = (
            f"[LINTRO] All output formats will be auto-generated in {self.run_dir}"
        )
        self.console_output(header_msg)
        logger.debug(f"Starting {action} with {tools_count} tools: {tools_list}")

    def print_tool_header(self, tool_name: str, action: str) -> None:
        """Print rich tool execution header with borders and emojis."""
        emoji = get_tool_emoji(tool_name)
        emojis = (emoji + " ") * 5

        border = "=" * 70
        header = f"✨  Running {tool_name} ({action})    {emojis}"

        self.console_output("")
        self.console_output(border)
        self.console_output(header)
        self.console_output(border)
        self.console_output("")

        logger.debug(f"Starting tool: {tool_name}")

    def print_tool_result(self, tool_name: str, output: str, issues_count: int) -> None:
        """Print tool results - either the output or success message."""
        if output and output.strip():
            self.console_output(output)
            logger.debug(f"Tool {tool_name} output: {len(output)} characters")
        else:
            logger.debug(f"Tool {tool_name} produced no output")

        # Print result status
        if issues_count == 0:
            self.success("✓ No issues found.")
        else:
            error_msg = f"✗ Found {issues_count} issues"
            self.console_output(error_msg, color="red")

        self.console_output("")  # Blank line after each tool

    def print_execution_summary(self, action: str, tool_results: list[Any]) -> None:
        """Print the execution summary with table and final status."""
        # Execution summary section
        summary_header = click.style("📋 EXECUTION SUMMARY", fg="cyan", bold=True)
        border_line = click.style("=" * 50, fg="cyan")

        self.console_output(summary_header)
        self.console_output(border_line)

        # Build summary table
        self._print_summary_table(action, tool_results)

        # Final status and ASCII art
        total_issues = sum(
            getattr(result, "issues_count", 0) for result in tool_results
        )
        self._print_final_status(action, total_issues)
        self._print_ascii_art(total_issues)

        logger.debug(f"{action} completed with {total_issues} total issues")

    def _print_summary_table(self, action: str, tool_results: list[Any]) -> None:
        """Print the execution summary table."""
        try:
            from tabulate import tabulate

            summary_data = []
            for result in tool_results:
                tool_name = getattr(result, "name", "unknown")
                issues_count = getattr(result, "issues_count", 0)

                emoji = get_tool_emoji(tool_name)
                tool_display = f"{emoji} {tool_name}"

                # For format operations, success means tool ran (regardless of fixes made)
                # For check operations, success means no issues found
                if action == "fmt":
                    # Format operations always succeed when they run
                    status_display = click.style("✅ PASS", fg="green", bold=True)
                    issues_display = click.style(
                        f"{issues_count} fixed" if issues_count > 0 else "0 fixed",
                        fg="green",
                        bold=True,
                    )
                else:  # check
                    status_display = (
                        click.style("✅ PASS", fg="green", bold=True)
                        if issues_count == 0
                        else click.style("❌ FAIL", fg="red", bold=True)
                    )
                    issues_display = click.style(
                        str(issues_count),
                        fg="green" if issues_count == 0 else "red",
                        bold=True,
                    )

                summary_data.append([tool_display, status_display, issues_display])

            headers = [
                click.style("Tool", fg="cyan", bold=True),
                click.style("Status", fg="cyan", bold=True),
                click.style("Issues", fg="cyan", bold=True),
            ]

            table = tabulate(
                summary_data, headers=headers, tablefmt="grid", stralign="left"
            )
            self.console_output(table)
            self.console_output("")

        except ImportError:
            # Fallback if tabulate not available
            self.console_output("Summary table requires tabulate package")
            logger.warning("tabulate not available for summary table")

    def _print_final_status(self, action: str, total_issues: int) -> None:
        """Print the final status message."""
        if action == "fmt":
            # Format operations: show success regardless of fixes made
            if total_issues == 0:
                final_msg = "✓ No issues found."
            else:
                final_msg = f"✓ Fixed {total_issues} issues."
            self.console_output(click.style(final_msg, fg="green", bold=True))
        else:  # check
            # Check operations: show failure if issues found
            if total_issues == 0:
                final_msg = "✓ No issues found."
                self.console_output(click.style(final_msg, fg="green", bold=True))
            else:
                final_msg = f"⚠️  TOTAL ISSUES: {total_issues}"
                self.console_output(click.style(final_msg, fg="red", bold=True))

        self.console_output("")

    def _print_ascii_art(self, total_issues: int) -> None:
        """Print ASCII art based on success/failure."""
        try:
            if total_issues == 0:
                ascii_art = read_ascii_art("success.txt")
            else:
                ascii_art = read_ascii_art("fail.txt")

            if ascii_art:
                art_text = "\n".join(ascii_art)
                self.console_output(art_text)
        except Exception as e:
            logger.debug(f"Could not load ASCII art: {e}")

    def print_verbose_info(
        self, action: str, tools_list: str, paths_list: str, output_format: str
    ) -> None:
        """Print verbose configuration information."""
        if not self.verbose:
            return

        info_border = "=" * 70
        info_title = (
            "🔧  Format Configuration" if action == "fmt" else "🔍  Check Configuration"
        )
        info_emojis = ("🔧 " if action == "fmt" else "🔍 ") * 5

        self.console_output(info_border)
        self.console_output(f"{info_title}    {info_emojis}")
        self.console_output(info_border)
        self.console_output("")

        self.console_output(f"🔧 Running tools: {tools_list}")
        self.console_output(
            f"📁 {'Formatting' if action == 'fmt' else 'Checking'} paths: {paths_list}"
        )
        self.console_output(f"📊 Output format: {output_format}")
        self.console_output("")

    def save_console_log(self) -> None:
        """Save tracked console messages to console.log."""
        console_log_path = self.run_dir / "console.log"
        with open(console_log_path, "w", encoding="utf-8") as f:
            for message in self.console_messages:
                f.write(f"{message}\n")
        logger.debug(f"Saved console output to {console_log_path}")


def create_logger(run_dir: Path, verbose: bool = False) -> SimpleLintroLogger:
    """Create a SimpleLintroLogger instance.

    Args:
        run_dir: Directory to write log files to
        verbose: Whether to enable verbose logging

    Returns:
        Configured SimpleLintroLogger instance
    """
    return SimpleLintroLogger(run_dir=run_dir, verbose=verbose)
