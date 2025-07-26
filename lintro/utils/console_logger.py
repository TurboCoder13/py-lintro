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
    """Simplified logger for lintro using Loguru with rich console output."""

    def __init__(self, run_dir: Path, verbose: bool = False, raw_output: bool = False):
        """Initialize the logger.

        Args:
            run_dir: Directory for log files.
            verbose: Whether to enable verbose logging.
            raw_output: Whether to show raw tool output instead of formatted output.
        """
        self.run_dir = run_dir
        self.verbose = verbose
        self.raw_output = raw_output
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
            format=(
                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                "{message}"
            ),
            colorize=True,
        )

        # Add debug.log handler (captures everything)
        debug_log_path = self.run_dir / "debug.log"
        logger.add(
            debug_log_path,
            level="DEBUG",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
            rotation=None,  # Don't rotate, each run gets its own file
        )

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message to the console.

        Args:
            message: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.

        Args:
            message: The debug message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message to the console.

        Args:
            message: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_messages.append(f"WARNING: {message}")
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message to the console.

        Args:
            message: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
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

    def success(self, message: str, **kwargs: Any) -> None:
        """Log a success message to the console.

        Args:
            message: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_output(message, color="green")
        logger.debug(f"SUCCESS: {message}")

    def print_lintro_header(
        self, action: str, tools_count: int, tools_list: str
    ) -> None:
        """Print the main LINTRO header.

        Args:
            action: The action being performed.
            tools_count: The number of tools being run.
            tools_list: The list of tools being run.
        """
        header_msg = (
            f"[LINTRO] All output formats will be auto-generated in {self.run_dir}"
        )
        self.console_output(header_msg)
        logger.debug(f"Starting {action} with {tools_count} tools: {tools_list}")

    def print_tool_header(self, tool_name: str, action: str) -> None:
        """Print the header for a tool's output.

        Args:
            tool_name: The name of the tool.
            action: The action being performed (e.g., 'check', 'fmt').
        """
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
        """Print the result for a tool.

        Args:
            tool_name: The name of the tool.
            output: The output from the tool.
            issues_count: The number of issues found.
        """
        if output and output.strip():
            # Display the output (either raw or formatted, depending on what was passed)
            self.console_output(output)
            logger.debug(f"Tool {tool_name} output: {len(output)} characters")
        else:
            logger.debug(f"Tool {tool_name} produced no output")

        # Print result status
        if issues_count == 0:
            # Check if the output indicates no files were processed
            if output and any(
                msg in output for msg in ["No files to", "No Python files found to"]
            ):
                self.console_output("⚠️  No files processed (excluded by patterns)")
            else:
                # For format operations, check if there are remaining issues that
                # couldn't be auto-fixed
                if output and "cannot be auto-fixed" in output.lower():
                    # Don't show "No issues found" if there are remaining issues
                    pass
                else:
                    self.success("✓ No issues found.")
        else:
            # For format operations, parse the output to show better messages
            if output and ("Fixed" in output or "issue(s)" in output):
                # This is a format operation - parse for better messaging
                import re

                # Look for fixed count
                fixed_match = re.search(r"Fixed (\d+) issue\(s\)", output)
                fixed_count = int(fixed_match.group(1)) if fixed_match else 0

                # Look for remaining count
                remaining_match = re.search(
                    r"Found (\d+) issue\(s\) that cannot be auto-fixed", output
                )
                remaining_count = (
                    int(remaining_match.group(1)) if remaining_match else 0
                )

                # Look for total initial count
                initial_match = re.search(r"Found (\d+) errors?", output)
                int(initial_match.group(1)) if initial_match else 0

                if fixed_count > 0 and remaining_count == 0:
                    self.success(f"✓ {fixed_count} fixed")
                elif fixed_count > 0 and remaining_count > 0:
                    self.console_output(f"✓ {fixed_count} fixed", color="green")
                    self.console_output(f"✗ {remaining_count} remaining", color="red")
                elif remaining_count > 0:
                    self.console_output(f"✗ {remaining_count} remaining", color="red")
                else:
                    # Fallback to original behavior
                    error_msg = f"✗ Found {issues_count} issues"
                    self.console_output(error_msg, color="red")
            else:
                # Regular check operation - always show issue count for check operations
                error_msg = f"✗ Found {issues_count} issues"
                self.console_output(error_msg, color="red")

        self.console_output("")  # Blank line after each tool

    def print_execution_summary(self, action: str, tool_results: list[Any]) -> None:
        """Print the execution summary for all tools.

        Args:
            action: The action being performed.
            tool_results: The list of tool results.
        """
        # Execution summary section
        summary_header = click.style("📋 EXECUTION SUMMARY", fg="cyan", bold=True)
        border_line = click.style("=" * 50, fg="cyan")

        self.console_output(summary_header)
        self.console_output(border_line)

        # Build summary table
        self._print_summary_table(action, tool_results)

        # Final status and ASCII art
        if action == "fmt":
            # For format commands, track both fixed and remaining issues
            total_fixed = sum(
                getattr(result, "issues_count", 0) for result in tool_results
            )
            total_remaining = 0
            for result in tool_results:
                output = getattr(result, "output", "")
                if output and (
                    "remaining" in output.lower()
                    or "cannot be auto-fixed" in output.lower()
                ):
                    # Look for patterns like "X remaining" or "X issue(s) that
                    # cannot be auto-fixed"
                    import re

                    # Try multiple patterns to match different output formats
                    remaining_match = re.search(
                        r"Found\s+(\d+)\s+issue\(s\)\s+that\s+cannot\s+be\s+auto-fixed",
                        output,
                    )
                    if not remaining_match:
                        remaining_match = re.search(
                            r"(\d+)\s+(?:issue\(s\)\s+)?(?:that\s+cannot\s+be\s+auto-fixed|remaining)",
                            output.lower(),
                        )
                    if remaining_match:
                        total_remaining += int(remaining_match.group(1))
                    elif not getattr(result, "success", True):
                        # If success is False and no specific count found,
                        # assume 1 remaining
                        total_remaining += 1

            self._print_final_status_format(total_fixed, total_remaining)
            self._print_ascii_art_format(total_remaining)
            logger.debug(
                f"{action} completed with {total_fixed} fixed, "
                f"{total_remaining} remaining"
            )
        else:
            # For check commands, use total issues
            total_issues = sum(
                getattr(result, "issues_count", 0) for result in tool_results
            )
            self._print_final_status(action, total_issues)
            self._print_ascii_art(total_issues)
            logger.debug(f"{action} completed with {total_issues} total issues")

    def _print_summary_table(self, action: str, tool_results: list[Any]) -> None:
        """Print the summary table for the run.

        Args:
            action: The action being performed.
            tool_results: The list of tool results.
        """
        try:
            from tabulate import tabulate

            summary_data = []
            for result in tool_results:
                tool_name = getattr(result, "name", "unknown")
                issues_count = getattr(result, "issues_count", 0)
                success = getattr(result, "success", True)

                emoji = get_tool_emoji(tool_name)
                tool_display = f"{emoji} {tool_name}"

                # For format operations, success means tool ran
                # (regardless of fixes made)
                # For check operations, success means no issues found
                if action == "fmt":
                    # Format operations: show fixed count and remaining status
                    if success:
                        status_display = click.style("✅ PASS", fg="green", bold=True)
                    else:
                        status_display = click.style("❌ FAIL", fg="red", bold=True)

                    # Check if files were excluded
                    result_output = getattr(result, "output", "")
                    if result_output and any(
                        msg in result_output
                        for msg in ["No files to", "No Python files found to"]
                    ):
                        fixed_display = click.style("SKIPPED", fg="yellow", bold=True)
                        remaining_display = click.style(
                            "SKIPPED", fg="yellow", bold=True
                        )
                    else:
                        # Parse output to determine remaining issues
                        remaining_count = 0
                        if result_output and (
                            "remaining" in result_output.lower()
                            or "cannot be auto-fixed" in result_output.lower()
                        ):
                            import re

                            # Try multiple patterns to match different output formats
                            remaining_match = re.search(
                                r"Found\s+(\d+)\s+issue\(s\)\s+that\s+cannot\s+be\s+auto-fixed",
                                result_output,
                            )
                            if not remaining_match:
                                remaining_match = re.search(
                                    r"(\d+)\s+(?:issue\(s\)\s+)?(?:that\s+cannot\s+be\s+auto-fixed|remaining)",
                                    result_output.lower(),
                                )
                            if remaining_match:
                                remaining_count = int(remaining_match.group(1))
                            elif not success:
                                remaining_count = 1

                        # Fixed issues display
                        if issues_count > 0:
                            fixed_display = click.style(
                                str(issues_count), fg="green", bold=True
                            )
                        else:
                            fixed_display = click.style("0", fg="green", bold=True)

                        # Remaining issues display
                        if remaining_count > 0:
                            remaining_display = click.style(
                                str(remaining_count), fg="red", bold=True
                            )
                        else:
                            remaining_display = click.style("0", fg="green", bold=True)
                else:  # check
                    status_display = (
                        click.style("✅ PASS", fg="green", bold=True)
                        if issues_count == 0
                        else click.style("❌ FAIL", fg="red", bold=True)
                    )
                    # Check if files were excluded
                    result_output = getattr(result, "output", "")
                    if result_output and any(
                        msg in result_output
                        for msg in ["No files to", "No Python files found to"]
                    ):
                        issues_display = click.style("SKIPPED", fg="yellow", bold=True)
                    else:
                        issues_display = click.style(
                            str(issues_count),
                            fg="green" if issues_count == 0 else "red",
                            bold=True,
                        )

                if action == "fmt":
                    summary_data.append(
                        [tool_display, status_display, fixed_display, remaining_display]
                    )
                else:
                    summary_data.append([tool_display, status_display, issues_display])

            # Set headers based on action
            if action == "fmt":
                headers = [
                    click.style("Tool", fg="cyan", bold=True),
                    click.style("Status", fg="cyan", bold=True),
                    click.style("Fixed", fg="cyan", bold=True),
                    click.style("Remaining", fg="cyan", bold=True),
                ]
            else:
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
        """Print the final status for the run.

        Args:
            action: The action being performed.
            total_issues: The total number of issues found.
        """
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
                final_msg = f"✗ Found {total_issues} issues"
                self.console_output(click.style(final_msg, fg="red", bold=True))

        self.console_output("")

    def _print_final_status_format(
        self, total_fixed: int, total_remaining: int
    ) -> None:
        """Print the final status for format operations.

        Args:
            total_fixed: The total number of issues fixed.
            total_remaining: The total number of remaining issues.
        """
        if total_remaining == 0:
            if total_fixed == 0:
                final_msg = "✓ No issues found."
            else:
                final_msg = f"✓ {total_fixed} fixed"
            self.console_output(click.style(final_msg, fg="green", bold=True))
        else:
            if total_fixed > 0:
                fixed_msg = f"✓ {total_fixed} fixed"
                self.console_output(click.style(fixed_msg, fg="green", bold=True))
            remaining_msg = f"✗ {total_remaining} remaining"
            self.console_output(click.style(remaining_msg, fg="red", bold=True))

        self.console_output("")

    def _print_ascii_art_format(self, total_remaining: int) -> None:
        """Print ASCII art for format operations based on remaining issues.

        Args:
            total_remaining: The total number of remaining issues.
        """
        try:
            if total_remaining == 0:
                ascii_art = read_ascii_art("success.txt")
            else:
                ascii_art = read_ascii_art("fail.txt")

            if ascii_art:
                art_text = "\n".join(ascii_art)
                self.console_output(art_text)
        except Exception as e:
            logger.debug(f"Could not load ASCII art: {e}")

    def _print_ascii_art(self, total_issues: int) -> None:
        """Print ASCII art based on the number of issues.

        Args:
            total_issues: The total number of issues found.
        """
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
        """Print verbose information about the run.

        Args:
            action: The action being performed.
            tools_list: The list of tools being run.
            paths_list: The list of paths being checked/formatted.
            output_format: The output format being used.
        """
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


def create_logger(
    run_dir: Path, verbose: bool = False, raw_output: bool = False
) -> SimpleLintroLogger:
    """Create a SimpleLintroLogger instance.

    Args:
        run_dir: Directory for log files.
        verbose: Whether to enable verbose logging.
        raw_output: Whether to show raw tool output instead of formatted output.

    Returns:
        Configured SimpleLintroLogger instance.
    """
    return SimpleLintroLogger(run_dir=run_dir, verbose=verbose, raw_output=raw_output)
