"""Console logger for lintro output formatting."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import click
from loguru import logger

from lintro.enums.action import Action, normalize_action
from lintro.enums.tool_name import ToolName
from lintro.utils.console_formatting import (
    BORDER_LENGTH,
    RE_CANNOT_AUTOFIX,
    RE_REMAINING_OR_CANNOT,
    get_tool_emoji,
)
from lintro.utils.display_helpers import (
    print_ascii_art,
    print_final_status,
    print_final_status_format,
)
from lintro.utils.summary_tables import print_summary_table

# Re-export for backwards compatibility
__all__ = ["ConsoleLogger", "get_tool_emoji"]


class ConsoleLogger:
    """Logger for console output formatting and display."""

    def __init__(self, run_dir: Path | None = None) -> None:
        """Initialize the ConsoleLogger.

        Args:
            run_dir: Optional run directory path for output location display.
        """
        self.run_dir = run_dir

    def console_output(self, text: str, color: str | None = None) -> None:
        """Display text on console.

        Args:
            text: str: Text to display.
            color: str | None: Optional color for the text.
        """
        if color:
            click.echo(click.style(text, fg=color))
        else:
            click.echo(text)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: str: Message to log.
        """
        self.console_output(message)

    def debug(self, message: str) -> None:
        """Log a debug message (only shown when debug logging is enabled).

        Args:
            message: str: Message to log.
        """
        logger.debug(message)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: str: Message to log.
        """
        self.console_output(message, color="yellow")

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: str: Message to log.
        """
        self.console_output(message, color="red")

    def success(self, message: str) -> None:
        """Log a success message.

        Args:
            message: str: Message to log.
        """
        self.console_output(f"✅ {message}", color="green")

    def save_console_log(self) -> None:
        """Create a console log file marker in the run directory.

        Note: Currently creates an empty file as a placeholder.
        """
        if self.run_dir:
            try:
                log_file = self.run_dir / "console.log"
                log_file.touch()
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to create console.log: {e}")

    def print_execution_summary(
        self,
        action: Action,
        tool_results: list[object],
    ) -> None:
        """Print the execution summary for all tools.

        Args:
            action: Action: The action being performed.
            tool_results: list[object]: The list of tool results.
        """
        # Add separation before Execution Summary
        self.console_output(text="")

        # Execution summary section
        summary_header: str = click.style("📋 EXECUTION SUMMARY", fg="cyan", bold=True)
        border_line: str = click.style("=" * 50, fg="cyan")

        self.console_output(text=summary_header)
        self.console_output(text=border_line)

        # Build summary table
        self._print_summary_table(action=action, tool_results=tool_results)

        # Totals line and ASCII art
        if action == Action.FIX:
            # For format commands, track both fixed and remaining issues
            # Use standardized counts when provided by tools
            total_fixed: int = 0
            total_remaining: int = 0
            for result in tool_results:
                fixed_std = getattr(result, "fixed_issues_count", None)
                remaining_std = getattr(result, "remaining_issues_count", None)
                success = getattr(result, "success", True)

                if fixed_std is not None:
                    total_fixed += fixed_std
                else:
                    total_fixed += getattr(result, "issues_count", 0)

                if remaining_std is not None:
                    # Skip sentinel values when calculating totals
                    if isinstance(remaining_std, int):
                        total_remaining += remaining_std
                    # If remaining_std is a string sentinel, don't add to total
                elif not success:
                    # Tool failed - treat as having remaining issues
                    # This covers execution errors, config errors, timeouts, etc.
                    # Use sentinel for individual display, but don't add to
                    # numeric total
                    pass  # Skip adding sentinel to total_remaining
                else:
                    # Fallback to parsing when standardized remaining isn't provided
                    output = getattr(result, "output", "")
                    if output and (
                        "remaining" in output.lower()
                        or "cannot be auto-fixed" in output.lower()
                    ):
                        remaining_match = RE_CANNOT_AUTOFIX.search(output)
                        if not remaining_match:
                            remaining_match = RE_REMAINING_OR_CANNOT.search(
                                output.lower(),
                            )
                        if remaining_match:
                            total_remaining += int(remaining_match.group(1))

            # Show totals line then ASCII art
            totals_line: str = (
                f"Totals: fixed={total_fixed}, remaining={total_remaining}"
            )
            self.console_output(text=click.style(totals_line, fg="cyan"))
            self._print_ascii_art(total_issues=total_remaining)
            logger.debug(
                f"{action} completed with {total_fixed} fixed, "
                f"{total_remaining} remaining",
            )
        else:
            # For check commands, use total issues; treat any tool failure as failure
            total_issues: int = sum(
                (getattr(result, "issues_count", 0) for result in tool_results),
            )
            any_failed: bool = any(
                not getattr(result, "success", True) for result in tool_results
            )
            total_for_art: int = (
                total_issues if not any_failed else max(1, total_issues)
            )
            # Show totals line then ASCII art
            totals_line_chk: str = f"Total issues: {total_issues}"
            self.console_output(text=click.style(totals_line_chk, fg="cyan"))
            self._print_ascii_art(total_issues=total_for_art)
            logger.debug(
                f"{action} completed with {total_issues} total issues"
                + (" and failures" if any_failed else ""),
            )

    def _print_summary_table(
        self,
        action: Action | str,
        tool_results: list[object],
    ) -> None:
        """Print the summary table for the run.

        Args:
            action: Action | str: The action being performed.
            tool_results: list[object]: The list of tool results.
        """
        # Convert to Action enum if string provided
        action_enum = normalize_action(action)
        print_summary_table(
            console_output_func=self.console_output,
            action=action_enum,
            tool_results=tool_results,
        )

    def _print_final_status(
        self,
        action: Action | str,
        total_issues: int,
    ) -> None:
        """Print the final status for the run.

        Args:
            action: Action | str: The action being performed.
            total_issues: int: The total number of issues found.
        """
        action_enum = normalize_action(action)
        print_final_status(
            console_output_func=self.console_output,
            action=action_enum,
            total_issues=total_issues,
        )

    def _print_final_status_format(
        self,
        total_fixed: int,
        total_remaining: int,
    ) -> None:
        """Print the final status for format operations.

        Args:
            total_fixed: int: The total number of issues fixed.
            total_remaining: int: The total number of remaining issues.
        """
        print_final_status_format(
            console_output_func=self.console_output,
            total_fixed=total_fixed,
            total_remaining=total_remaining,
        )

    def _print_ascii_art(
        self,
        total_issues: int,
    ) -> None:
        """Print ASCII art based on the number of issues.

        Args:
            total_issues: int: The total number of issues found.
        """
        print_ascii_art(
            console_output_func=self.console_output,
            issue_count=total_issues,
        )

    def print_lintro_header(self) -> None:
        """Print the main Lintro header with output directory information."""
        if self.run_dir:
            header_msg: str = (
                f"[LINTRO] All output formats will be auto-generated in {self.run_dir}"
            )
            self.console_output(text=header_msg)
            self.console_output(text="")

    def print_tool_header(
        self,
        tool_name: str,
        action: str,
    ) -> None:
        """Print a formatted header for a tool execution.

        Args:
            tool_name: str: Name of the tool.
            action: str: The action being performed ("check" or "fmt").
        """
        emoji: str = get_tool_emoji(tool_name)
        border: str = "=" * BORDER_LENGTH
        header_text: str = (
            f"✨  Running {tool_name} ({action})    "
            f"{emoji} {emoji} {emoji} {emoji} {emoji}"
        )

        self.console_output(text=border)
        self.console_output(text=header_text)
        self.console_output(text=border)
        self.console_output(text="")

    def print_tool_result(
        self,
        tool_name: str,
        output: str,
        issues_count: int,
        raw_output_for_meta: str | None = None,
        action: Action | None = None,
        success: bool = True,
    ) -> None:
        """Print the result of a tool execution.

        Args:
            tool_name: str: Name of the tool.
            output: str: Tool output to display.
            issues_count: int: Number of issues found.
            raw_output_for_meta: str | None: Raw output for metadata parsing.
            action: Action | None: Action being performed.
            success: bool: Whether the tool execution was successful.
        """
        if output:
            self.console_output(text=output)
            self.console_output(text="")

        # Parse raw output for additional metadata messages
        if raw_output_for_meta and action == Action.CHECK:
            self._print_metadata_messages(raw_output_for_meta)

        # Special handling for test results
        if action == Action.TEST and tool_name == ToolName.PYTEST.value:
            self._print_pytest_results(output, success)

    def _print_metadata_messages(self, raw_output: str) -> None:
        """Print metadata messages parsed from raw tool output.

        Uses consistent message format with standardized prefixes for all output.

        Args:
            raw_output: str: Raw tool output to parse for metadata.
        """
        # Pattern-to-message mapping for consistent formatting
        # Order matters: more specific patterns should be checked first
        output_lower = raw_output.lower()

        # Look for fixable issues with count
        fixable_match = re.search(r"(\d+)\s*fixable", output_lower)
        if fixable_match:
            fixable_count = int(fixable_match.group(1))
            if fixable_count > 0:
                self.console_output(
                    text=f"Info: Found {fixable_count} auto-fixable issue(s)",
                )
            else:
                self.console_output(text="Info: No issues found")
            return

        # Check for non-fixable issues
        if "cannot be auto-fixed" in output_lower:
            self.console_output(text="Info: Found issues that cannot be auto-fixed")
            return

        # Check for formatting suggestions
        if "would reformat" in output_lower:
            self.console_output(text="Info: Files would be reformatted")
            return

        # Check for fixed issues
        if "fixed" in output_lower:
            self.console_output(text="Info: Issues were fixed")
            return

        # Default: no specific patterns found
        self.console_output(text="Info: No issues found")

    def _print_pytest_results(self, output: str, success: bool) -> None:
        """Print formatted pytest results.

        Args:
            output: str: Pytest output.
            success: bool: Whether tests passed.
        """
        self.console_output(text="")
        self.console_output(text="📋 Test Results", color="cyan")
        self.console_output(text="=" * 50, color="cyan")

        if success:
            self.console_output(text="✅ All tests passed", color="green")
        else:
            self.console_output(text="❌ Some tests failed", color="red")

        if output:
            self.console_output(text="")
            self.console_output(text=output)

    def print_post_checks_header(
        self,
    ) -> None:
        """Print a distinct header separating the post-checks phase."""
        # Use a heavy unicode border and magenta coloring to stand out
        border_char: str = "━"
        border: str = border_char * BORDER_LENGTH
        title_styled: str = click.style(
            text="🚦  POST-CHECKS",
            fg="magenta",
            bold=True,
        )
        subtitle_styled: str = click.style(
            text=("Running optional follow-up checks after primary tools"),
            fg="magenta",
        )
        border_styled: str = click.style(text=border, fg="magenta")

        self.console_output(text=border_styled)
        self.console_output(text=title_styled)
        self.console_output(text=subtitle_styled)
        self.console_output(text=border_styled)
        self.console_output(text="")


def create_logger(run_dir: Path | None = None, **kwargs: Any) -> ConsoleLogger:
    """Create a new ConsoleLogger instance.

    Args:
        run_dir: Path | None: Optional run directory path for output location display.
        **kwargs: Additional arguments (ignored for backward compatibility).

    Returns:
        ConsoleLogger: A new instance of ConsoleLogger.
    """
    return ConsoleLogger(run_dir=run_dir)


# Backward compatibility alias
SimpleLintroLogger = ConsoleLogger
