"""Simplified Loguru-based logging utility for Lintro.

Single responsibility: Handle console display and file logging using Loguru.
No tee, no stream redirection, clean and simple with rich formatting.
"""

import re
import sys
from pathlib import Path

import click
from loguru import logger

from lintro.utils.formatting import read_ascii_art

# Constants
TOOL_EMOJIS: dict[str, str] = {
    "ruff": "🦀",
    "prettier": "💅",
    "darglint": "📝",
    "hadolint": "🐳",
    "yamllint": "📄",
    "black": "🖤",
    "pytest": "🧪",
}
DEFAULT_EMOJI: str = "🔧"
BORDER_LENGTH: int = 70
INFO_BORDER_LENGTH: int = 70
DEFAULT_REMAINING_COUNT: int = 1


# Regex patterns used to parse tool outputs for remaining issue counts
# Centralized to avoid repeated long literals and to keep matching logic
# consistent across the module.
RE_CANNOT_AUTOFIX: re.Pattern[str] = re.compile(
    r"Found\s+(\d+)\s+issue\(s\)\s+that\s+cannot\s+be\s+auto-fixed",
)
RE_REMAINING_OR_CANNOT: re.Pattern[str] = re.compile(
    r"(\d+)\s+(?:issue\(s\)\s+)?(?:that\s+cannot\s+be\s+auto-fixed|remaining)",
)


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a tool.

    Args:
        tool_name: str: Name of the tool.

    Returns:
        str: Emoji for the tool.
    """
    return TOOL_EMOJIS.get(tool_name, DEFAULT_EMOJI)


class SimpleLintroLogger:
    """Simplified logger for lintro using Loguru with rich console output."""

    def __init__(
        self,
        run_dir: Path,
        verbose: bool = False,
        raw_output: bool = False,
    ) -> None:
        """Initialize the logger.

        Args:
            run_dir: Path: Directory for log files.
            verbose: bool: Whether to enable verbose logging.
            raw_output: bool: Whether to show raw tool output instead of \
                formatted output.
        """
        self.run_dir = run_dir
        self.verbose = verbose
        self.raw_output = raw_output
        self.console_messages: list[str] = []  # Track console output for console.log

        # Configure Loguru
        self._setup_loguru()

    @staticmethod
    def _get_summary_value(
        summary: dict | object,
        key: str,
        default: int | float = 0,
    ) -> int | float:
        """Extract value from summary dict or object.

        Args:
            summary: Summary data as dict or dataclass.
            key: Attribute/key name.
            default: Default value if not found.

        Returns:
            int | float: The extracted value or default.
        """
        if isinstance(summary, dict):
            return summary.get(key, default)
        return getattr(summary, key, default)

    def _setup_loguru(self) -> None:
        """Configure Loguru with clean, simple handlers."""
        # Remove default handler
        logger.remove()

        # Add console handler (for immediate display)
        # Only capture WARNING and ERROR for console
        logger.add(
            sys.stderr,
            level="WARNING",  # Only show warnings and errors
            format="{message}",  # Simple format without timestamps/log levels
            colorize=True,
        )

        # Add debug.log handler (captures everything)
        debug_log_path: Path = self.run_dir / "debug.log"
        logger.add(
            debug_log_path,
            level="DEBUG",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
            rotation=None,  # Don't rotate, each run gets its own file
        )

    def info(self, message: str, **kwargs) -> None:
        """Log an info message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def info_blue(self, message: str, **kwargs) -> None:
        """Log an info message to the console in blue color.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        styled_message = click.style(message, fg="cyan", bold=True)
        click.echo(styled_message)
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message.

        Args:
            message: str: The debug message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_messages.append(f"WARNING: {message}")
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_messages.append(f"ERROR: {message}")
        logger.error(message, **kwargs)

    def console_output(
        self,
        text: str,
        color: str | None = None,
    ) -> None:
        """Display text on console and track for console.log.

        Args:
            text: str: Text to display.
            color: str | None: Optional color for the text.
        """
        if color:
            click.echo(click.style(text, fg=color))
        else:
            click.echo(text)

        # Track for console.log (without color codes)
        self.console_messages.append(text)

    def success(self, message: str, **kwargs) -> None:
        """Log a success message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        self.console_output(text=message, color="green")
        logger.debug(f"SUCCESS: {message}")

    def print_lintro_header(
        self,
        action: str,
        tool_count: int,
        tools_list: str,
    ) -> None:
        """Print the main LINTRO header.

        Args:
            action: str: The action being performed.
            tool_count: int: The number of tools being run.
            tools_list: str: The list of tools being run.
        """
        header_msg: str = click.style(
            f"[LINTRO] All output formats will be auto-generated in {self.run_dir}",
            fg="cyan",
            bold=True,
        )
        self.console_output(text=header_msg)
        logger.debug(f"Starting {action} with {tool_count} tools: {tools_list}")

    def print_tool_header(
        self,
        tool_name: str,
        action: str,
    ) -> None:
        """Print the header for a tool's output.

        Args:
            tool_name: str: The name of the tool.
            action: str: The action being performed (e.g., 'check', 'fmt').
        """
        emoji: str = get_tool_emoji(tool_name)
        emojis: str = (emoji + " ") * 5

        border: str = "=" * BORDER_LENGTH
        header: str = f"✨  Running {tool_name} ({action})    {emojis}"

        self.console_output(text="")
        self.console_output(text=border)
        self.console_output(text=header)
        self.console_output(text=border)
        self.console_output(text="")

        logger.debug(f"Starting tool: {tool_name}")

    def print_post_checks_header(
        self,
        action: str,
    ) -> None:
        """Print a distinct header separating the post-checks phase.

        Args:
            action: str: The action being performed (e.g., 'check', 'fmt').
        """
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

        self.console_output(text="")
        self.console_output(text=border, color="magenta")
        self.console_output(text=title_styled)
        self.console_output(text=subtitle_styled)
        self.console_output(text=border, color="magenta")
        self.console_output(text="")

    def print_tool_result(
        self,
        tool_name: str,
        output: str,
        issues_count: int,
        raw_output_for_meta: str | None = None,
        action: str = "check",
        success: bool | None = None,
    ) -> None:
        """Print the result for a tool.

        Args:
            tool_name: str: The name of the tool.
            output: str: The output from the tool.
            issues_count: int: The number of issues found.
            raw_output_for_meta: str | None: Raw tool output used to extract
                fixable/remaining hints when available.
            action: str: The action being performed ("check" or "fmt").
            success: bool | None: Whether the tool run succeeded. When False,
                the result is treated as a failure even if no issues were
                counted (e.g., parse or runtime errors).
        """
        # Add section header for pytest/test results
        if tool_name.lower() == "pytest":
            self.console_output(text="")
            self.console_output(text="🧪 Test Results")
            self.console_output(text="-" * INFO_BORDER_LENGTH)

            # Display formatted test failures table if present
            # Skip JSON lines but keep tables
            if output and output.strip():
                lines = output.split("\n")
                display_lines = []
                skip_json = False
                for line in lines:
                    if line.startswith("{"):
                        # Skip JSON summary line
                        skip_json = True
                        continue
                    if skip_json and line.strip() == "":
                        # Skip blank line after JSON
                        skip_json = False
                        continue
                    if skip_json:
                        # Skip remaining JSON content
                        continue
                    # Keep everything else including table headers and content
                    display_lines.append(line)

                if display_lines:
                    self.console_output(text="\n".join(display_lines))

            # Don't show summary line here - it will be in the Execution Summary table
            if issues_count == 0 and not output:
                self.success(message="✓ No issues found.")

            return

        if output and output.strip():
            # Display the output (either raw or formatted, depending on what was passed)
            self.console_output(text=output)
            logger.debug(f"Tool {tool_name} output: {len(output)} characters")
        else:
            logger.debug(f"Tool {tool_name} produced no output")

        # Print result status
        if issues_count == 0:
            # For format action, prefer consolidated fixed summary if present
            if action == "fmt" and output and output.strip():
                # If output contains a consolidated fixed count, surface it
                m_fixed = re.search(r"Fixed (\d+) issue\(s\)", output)
                m_remaining = re.search(
                    r"Found (\d+) issue\(s\) that cannot be auto-fixed",
                    output,
                )
                fixed_val = int(m_fixed.group(1)) if m_fixed else 0
                remaining_val = int(m_remaining.group(1)) if m_remaining else 0
                if fixed_val > 0 or remaining_val > 0:
                    if fixed_val > 0:
                        self.console_output(text=f"✓ {fixed_val} fixed", color="green")
                    if remaining_val > 0:
                        self.console_output(
                            text=f"✗ {remaining_val} remaining",
                            color="red",
                        )
                    return

            # If the tool reported a failure (e.g., parse error), do not claim pass
            if success is False:
                self.console_output(text="✗ Tool execution failed", color="red")
            # Check if the output indicates no files were processed
            elif output and any(
                (msg in output for msg in ["No files to", "No Python files found to"]),
            ):
                self.console_output(
                    text=("⚠️  No files processed (excluded by patterns)"),
                )
            else:
                # For format operations, check if there are remaining issues that
                # couldn't be auto-fixed
                if output and "cannot be auto-fixed" in output.lower():
                    # Don't show "No issues found" if there are remaining issues
                    pass
                else:
                    self.success(message="✓ No issues found.")
        else:
            # For format operations, parse the output to show better messages
            if output and ("Fixed" in output or "issue(s)" in output):
                # This is a format operation - parse for better messaging
                # Prefer standardized counters if present in the output object
                fixed_count: int = (
                    getattr(output, "fixed_issues_count", None)
                    if hasattr(output, "fixed_issues_count")
                    else None
                )
                remaining_count: int = (
                    getattr(output, "remaining_issues_count", None)
                    if hasattr(output, "remaining_issues_count")
                    else None
                )
                initial_count: int = (
                    getattr(output, "initial_issues_count", None)
                    if hasattr(output, "initial_issues_count")
                    else None
                )

                # Fallback to regex parsing when standardized counts are not available
                if fixed_count is None:
                    fixed_match = re.search(r"Fixed (\d+) issue\(s\)", output)
                    fixed_count = int(fixed_match.group(1)) if fixed_match else 0
                if remaining_count is None:
                    remaining_match = re.search(
                        r"Found (\d+) issue\(s\) that cannot be auto-fixed",
                        output,
                    )
                    remaining_count = (
                        int(remaining_match.group(1)) if remaining_match else 0
                    )
                if initial_count is None:
                    initial_match = re.search(r"Found (\d+) errors?", output)
                    initial_count = int(initial_match.group(1)) if initial_match else 0

                if fixed_count > 0 and remaining_count == 0:
                    self.success(message=f"✓ {fixed_count} fixed")
                elif fixed_count > 0 and remaining_count > 0:
                    self.console_output(
                        text=f"✓ {fixed_count} fixed",
                        color="green",
                    )
                    self.console_output(
                        text=f"✗ {remaining_count} remaining",
                        color="red",
                    )
                elif remaining_count > 0:
                    self.console_output(
                        text=f"✗ {remaining_count} remaining",
                        color="red",
                    )
                elif initial_count > 0:
                    # If we found initial issues but no specific fixed/remaining counts,
                    # show the initial count as found
                    self.console_output(
                        text=f"✗ Found {initial_count} issues",
                        color="red",
                    )
                else:
                    # Fallback to original behavior
                    error_msg: str = f"✗ Found {issues_count} issues"
                    self.console_output(text=error_msg, color="red")
            else:
                # Show issue count with action-aware phrasing
                if action == "fmt":
                    error_msg: str = f"✗ {issues_count} issue(s) cannot be auto-fixed"
                else:
                    error_msg = f"✗ Found {issues_count} issues"
                self.console_output(text=error_msg, color="red")

                # Check if there are fixable issues and show warning
                raw_text = (
                    raw_output_for_meta if raw_output_for_meta is not None else output
                )
                # Sum all fixable counts if multiple sections are present
                if raw_text and action != "fmt":
                    # Sum any reported fixable lint issues
                    matches = re.findall(r"\[\*\]\s+(\d+)\s+fixable", raw_text)
                    fixable_count: int = sum(int(m) for m in matches) if matches else 0
                    # Add formatting issues as fixable by fmt when ruff reports them
                    if tool_name == "ruff" and (
                        "Formatting issues:" in raw_text or "Would reformat" in raw_text
                    ):
                        # Count files listed in 'Would reformat:' lines
                        reformat_files = re.findall(r"Would reformat:\s+(.+)", raw_text)
                        fixable_count += len(reformat_files)
                        # Or try summary line like: "N files would be reformatted"
                        if fixable_count == 0:
                            m_sum = re.search(
                                r"(\d+)\s+file(?:s)?\s+would\s+be\s+reformatted",
                                raw_text,
                            )
                            if m_sum:
                                fixable_count += int(m_sum.group(1))

                    if fixable_count > 0:
                        hint_a: str = "💡 "
                        hint_b: str = (
                            f"{fixable_count} formatting/linting issue(s) "
                            "can be auto-fixed "
                        )
                        hint_c: str = "with `lintro format`"
                        self.console_output(
                            text=hint_a + hint_b + hint_c,
                            color="yellow",
                        )

        # Remove redundant tip; consolidated above as a single auto-fix message

        self.console_output(text="")  # Blank line after each tool

    def print_execution_summary(
        self,
        action: str,
        tool_results: list[object],
    ) -> None:
        """Print the execution summary for all tools.

        Args:
            action: str: The action being performed ("check" or "fmt").
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
        if action == "fmt":
            # For format commands, track both fixed and remaining issues
            # Use standardized counts when provided by tools
            total_fixed: int = 0
            total_remaining: int = 0
            for result in tool_results:
                fixed_std = getattr(result, "fixed_issues_count", None)
                remaining_std = getattr(result, "remaining_issues_count", None)
                if fixed_std is not None:
                    total_fixed += fixed_std
                else:
                    total_fixed += getattr(result, "issues_count", 0)

                if remaining_std is not None:
                    total_remaining += remaining_std
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
                        elif not getattr(result, "success", True):
                            total_remaining += DEFAULT_REMAINING_COUNT

            # Show totals line then ASCII art
            totals_line: str = (
                f"Totals: fixed={total_fixed}, remaining={total_remaining}"
            )
            self.console_output(text=click.style(totals_line, fg="cyan"))
            self._print_ascii_art_format(total_remaining=total_remaining)
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
        action: str,
        tool_results: list[object],
    ) -> None:
        """Print the summary table for the run.

        Args:
            action: str: The action being performed.
            tool_results: list[object]: The list of tool results.
        """
        try:
            from tabulate import tabulate

            summary_data: list[list[str]] = []
            for result in tool_results:
                tool_name: str = getattr(result, "name", "unknown")
                issues_count: int = getattr(result, "issues_count", 0)
                success: bool = getattr(result, "success", True)

                emoji: str = get_tool_emoji(tool_name)
                tool_display: str = f"{emoji} {tool_name}"

                # Special handling for pytest/test action
                if action == "test" and tool_name.lower() == "pytest":
                    pytest_summary = getattr(result, "pytest_summary", None)
                    if pytest_summary:
                        # Use pytest summary data for more detailed display
                        passed = int(
                            self._get_summary_value(pytest_summary, "passed", 0),
                        )
                        failed = int(
                            self._get_summary_value(pytest_summary, "failed", 0),
                        )
                        skipped = int(
                            self._get_summary_value(pytest_summary, "skipped", 0),
                        )
                        docker_skipped = int(
                            self._get_summary_value(
                                pytest_summary,
                                "docker_skipped",
                                0,
                            ),
                        )
                        duration = float(
                            self._get_summary_value(pytest_summary, "duration", 0.0),
                        )
                        total = int(
                            self._get_summary_value(pytest_summary, "total", 0),
                        )

                        # Create detailed status display
                        status_display = (
                            click.style("✅ PASS", fg="green", bold=True)
                            if failed == 0
                            else click.style("❌ FAIL", fg="red", bold=True)
                        )

                        # Format duration with proper units
                        duration_str = f"{duration:.2f}s"

                        # Format skipped count to include docker skipped info
                        if docker_skipped > 0:
                            skipped_display = f"{skipped} ({docker_skipped} docker)"
                        else:
                            skipped_display = str(skipped)

                        # Create row with separate columns for each metric
                        summary_data.append(
                            [
                                tool_display,
                                status_display,
                                str(passed),
                                str(failed),
                                skipped_display,
                                str(total),
                                duration_str,
                            ],
                        )
                        continue

                # For format operations, success means tool ran
                # (regardless of fixes made)
                # For check operations, success means no issues found
                if action == "fmt":
                    # Format operations: show fixed count and remaining status
                    if success:
                        status_display: str = click.style(
                            "✅ PASS",
                            fg="green",
                            bold=True,
                        )
                    else:
                        status_display = click.style("❌ FAIL", fg="red", bold=True)

                    # Check if files were excluded
                    result_output: str = getattr(result, "output", "")
                    if result_output and any(
                        (
                            msg in result_output
                            for msg in ["No files to", "No Python files found to"]
                        ),
                    ):
                        fixed_display: str = click.style(
                            "SKIPPED",
                            fg="yellow",
                            bold=True,
                        )
                        remaining_display: str = click.style(
                            "SKIPPED",
                            fg="yellow",
                            bold=True,
                        )
                    else:
                        # Prefer standardized counts from ToolResult
                        remaining_std = getattr(result, "remaining_issues_count", None)
                        fixed_std = getattr(result, "fixed_issues_count", None)

                        if remaining_std is not None:
                            remaining_count: int = int(remaining_std)
                        else:
                            # Parse output to determine remaining issues
                            remaining_count = 0
                            if result_output and (
                                "remaining" in result_output.lower()
                                or "cannot be auto-fixed" in result_output.lower()
                            ):
                                # Try multiple patterns to match different
                                # output formats
                                remaining_match = RE_CANNOT_AUTOFIX.search(
                                    result_output,
                                )
                                if not remaining_match:
                                    remaining_match = RE_REMAINING_OR_CANNOT.search(
                                        result_output.lower(),
                                    )
                                if remaining_match:
                                    remaining_count = int(remaining_match.group(1))
                                elif not success:
                                    remaining_count = DEFAULT_REMAINING_COUNT

                        if fixed_std is not None:
                            fixed_display_value = int(fixed_std)
                        else:
                            # Fall back to issues_count when fixed is unknown
                            fixed_display_value = int(issues_count)

                        # Fixed issues display
                        fixed_display = click.style(
                            str(fixed_display_value),
                            fg="green",
                            bold=True,
                        )

                        # Remaining issues display
                        remaining_display = click.style(
                            str(remaining_count),
                            fg="red" if remaining_count > 0 else "green",
                            bold=True,
                        )
                else:  # check
                    # Check if this is an execution failure (timeout/error)
                    # vs linting issues
                    result_output = getattr(result, "output", "")
                    has_execution_failure = result_output and (
                        "timeout" in result_output.lower()
                        or "error processing" in result_output.lower()
                        or "tool execution failed" in result_output.lower()
                    )

                    # If there are execution failures but no parsed issues,
                    # show special status
                    if has_execution_failure and issues_count == 0:
                        # This shouldn't happen with our fix, but handle gracefully
                        status_display = click.style("❌ FAIL", fg="red", bold=True)
                    elif not success and issues_count == 0:
                        # Execution failure with no issues parsed - show as failure
                        status_display = click.style("❌ FAIL", fg="red", bold=True)
                    else:
                        status_display = (
                            click.style("✅ PASS", fg="green", bold=True)
                            if (success and issues_count == 0)
                            else click.style("❌ FAIL", fg="red", bold=True)
                        )
                    # Check if files were excluded
                    if result_output and any(
                        (
                            msg in result_output
                            for msg in ["No files to", "No Python files found to"]
                        ),
                    ):
                        issues_display: str = click.style(
                            "SKIPPED",
                            fg="yellow",
                            bold=True,
                        )
                    elif not success and issues_count == 0:
                        # Tool failed to execute properly - show ERROR indicator
                        # instead of misleading 0 count
                        issues_display = click.style(
                            "ERROR",
                            fg="red",
                            bold=True,
                        )
                    else:
                        issues_display = click.style(
                            str(issues_count),
                            fg="green" if issues_count == 0 else "red",
                            bold=True,
                        )

                if action == "fmt":
                    summary_data.append(
                        [
                            tool_display,
                            status_display,
                            fixed_display,
                            remaining_display,
                        ],
                    )
                else:
                    summary_data.append([tool_display, status_display, issues_display])

            # Set headers based on action
            # Use plain headers to avoid ANSI/emojis width misalignment
            headers: list[str]
            if action == "test":
                # Special table for test action with separate columns for test metrics
                headers = [
                    "Tool",
                    "Status",
                    "Passed",
                    "Failed",
                    "Skipped",
                    "Total",
                    "Duration",
                ]
            elif action == "fmt":
                headers = ["Tool", "Status", "Fixed", "Remaining"]
            else:
                headers = ["Tool", "Status", "Issues"]

            # Render with plain values to ensure proper alignment across terminals
            table: str = tabulate(
                tabular_data=summary_data,
                headers=headers,
                tablefmt="grid",
                stralign="left",
                disable_numparse=True,
            )
            self.console_output(text=table)
            self.console_output(text="")

        except ImportError:
            # Fallback if tabulate not available
            self.console_output(text="Summary table requires tabulate package")
            logger.warning("tabulate not available for summary table")

    def _print_final_status(
        self,
        action: str,
        total_issues: int,
    ) -> None:
        """Print the final status for the run.

        Args:
            action: str: The action being performed.
            total_issues: int: The total number of issues found.
        """
        if action == "fmt":
            # Format operations: show success regardless of fixes made
            if total_issues == 0:
                final_msg: str = "✓ No issues found."
            else:
                final_msg = f"✓ Fixed {total_issues} issues."
            self.console_output(text=click.style(final_msg, fg="green", bold=True))
        else:  # check
            # Check operations: show failure if issues found
            if total_issues == 0:
                final_msg = "✓ No issues found."
                self.console_output(text=click.style(final_msg, fg="green", bold=True))
            else:
                final_msg = f"✗ Found {total_issues} issues"
                self.console_output(text=click.style(final_msg, fg="red", bold=True))

        self.console_output(text="")

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
        if total_remaining == 0:
            if total_fixed == 0:
                final_msg: str = "✓ No issues found."
            else:
                final_msg = f"✓ {total_fixed} fixed"
            self.console_output(text=click.style(final_msg, fg="green", bold=True))
        else:
            if total_fixed > 0:
                fixed_msg: str = f"✓ {total_fixed} fixed"
                self.console_output(text=click.style(fixed_msg, fg="green", bold=True))
            remaining_msg: str = f"✗ {total_remaining} remaining"
            self.console_output(text=click.style(remaining_msg, fg="red", bold=True))

        self.console_output(text="")

    def _print_ascii_art_format(
        self,
        total_remaining: int,
    ) -> None:
        """Print ASCII art for format operations based on remaining issues.

        Args:
            total_remaining: int: The total number of remaining issues.
        """
        try:
            if total_remaining == 0:
                ascii_art = read_ascii_art(filename="success.txt")
            else:
                ascii_art = read_ascii_art(filename="fail.txt")

            if ascii_art:
                art_text: str = "\n".join(ascii_art)
                self.console_output(text=art_text)
        except Exception as e:
            logger.debug(f"Could not load ASCII art: {e}")

    def _print_ascii_art(
        self,
        total_issues: int,
    ) -> None:
        """Print ASCII art based on the number of issues.

        Args:
            total_issues: int: The total number of issues found.
        """
        try:
            if total_issues == 0:
                ascii_art = read_ascii_art(filename="success.txt")
            else:
                ascii_art = read_ascii_art(filename="fail.txt")

            if ascii_art:
                art_text: str = "\n".join(ascii_art)
                self.console_output(text=art_text)
        except Exception as e:
            logger.debug(f"Could not load ASCII art: {e}")

    def print_verbose_info(
        self,
        action: str,
        tools_list: str,
        paths_list: str,
        output_format: str,
    ) -> None:
        """Print verbose information about the run.

        Args:
            action: str: The action being performed.
            tools_list: str: The list of tools being run.
            paths_list: str: The list of paths being checked/formatted.
            output_format: str: The output format being used.
        """
        if not self.verbose:
            return

        info_border: str = "=" * INFO_BORDER_LENGTH
        info_title: str = (
            "🔧  Format Configuration" if action == "fmt" else "🔍  Check Configuration"
        )
        info_emojis: str = ("🔧 " if action == "fmt" else "🔍 ") * 5

        self.console_output(text=info_border)
        self.console_output(text=f"{info_title}    {info_emojis}")
        self.console_output(text=info_border)
        self.console_output(text="")

        self.console_output(text=f"🔧 Running tools: {tools_list}")
        self.console_output(
            text=(
                f"📁 {'Formatting' if action == 'fmt' else 'Checking'} "
                f"paths: {paths_list}"
            ),
        )
        self.console_output(text=f"📊 Output format: {output_format}")
        self.console_output(text="")

    def save_console_log(
        self,
    ) -> None:
        """Save tracked console messages to console.log."""
        console_log_path: Path = self.run_dir / "console.log"
        with open(console_log_path, "w", encoding="utf-8") as f:
            for message in self.console_messages:
                f.write(f"{message}\n")
        logger.debug(f"Saved console output to {console_log_path}")


def create_logger(
    run_dir: Path,
    verbose: bool = False,
    raw_output: bool = False,
) -> SimpleLintroLogger:
    """Create a SimpleLintroLogger instance.

    Args:
        run_dir: Path: Directory for log files.
        verbose: bool: Whether to enable verbose logging.
        raw_output: bool: Whether to show raw tool output instead of formatted output.

    Returns:
        SimpleLintroLogger: Configured SimpleLintroLogger instance.
    """
    return SimpleLintroLogger(
        run_dir=run_dir,
        verbose=verbose,
        raw_output=raw_output,
    )
