"""Result formatting utilities for Lintro tool output.

Handles formatting and display of individual tool results with rich colors and
status messages.
"""

import re
from typing import cast

from loguru import logger

from lintro.enums.action import Action, normalize_action
from lintro.enums.tool_name import ToolName


def print_tool_result(
    console_output_func: callable,
    success_func: callable,
    tool_name: str,
    output: str,
    issues_count: int,
    raw_output_for_meta: str | None = None,
    action: str | Action = "check",
    success: bool | None = None,
) -> None:
    """Print the result for a tool.

    Args:
        console_output_func: Function to output text to console
        success_func: Function to display success message
        tool_name: str: The name of the tool.
        output: str: The output from the tool.
        issues_count: int: The number of issues found.
        raw_output_for_meta: str | None: Raw tool output used to extract
            fixable/remaining hints when available.
        action: str | Action: The action being performed ("check", "fmt", "test").
        success: bool | None: Whether the tool run succeeded. When False,
            the result is treated as a failure even if no issues were
            counted (e.g., parse or runtime errors).
    """
    # Normalize action to enum
    action = normalize_action(action)

    # Add section header for pytest/test results
    if tool_name.lower() == ToolName.PYTEST:
        console_output_func(text="")
        console_output_func(text="🧪 Test Results")
        console_output_func(text="-" * 20)  # Simplified border length

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
                console_output_func(text="\n".join(display_lines))

        # Don't show summary line here - it will be in the Execution Summary table
        if issues_count == 0 and not output:
            success_func(message="✓ No issues found.")

        return

    if output and output.strip():
        # Display the output (either raw or formatted, depending on what was passed)
        console_output_func(text=output)
        logger.debug(f"Tool {tool_name} output: {len(output)} characters")
    else:
        logger.debug(f"Tool {tool_name} produced no output")

    # Print result status
    if issues_count == 0:
        # For format action, prefer consolidated fixed summary if present
        if action == Action.FIX and output and output.strip():
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
                    console_output_func(text=f"✓ {fixed_val} fixed", color="green")
                if remaining_val > 0:
                    console_output_func(
                        text=f"✗ {remaining_val} remaining",
                        color="red",
                    )
                return

        # If the tool reported a failure (e.g., parse error), do not claim pass
        if success is False:
            console_output_func(text="✗ Tool execution failed", color="red")
        # Check if the output indicates no files were processed
        elif output and any(
            (msg in output for msg in ["No files to", "No Python files found to"]),
        ):
            console_output_func(
                text=("⚠️  No files processed (excluded by patterns)"),
            )
        else:
            # For format operations, check if there are remaining issues that
            # couldn't be auto-fixed
            if output and "cannot be auto-fixed" in output.lower():
                # Don't show "No issues found" if there are remaining issues
                pass
            else:
                success_func(message="✓ No issues found.")
    else:
        # For format operations, parse the output to show better messages
        if output and ("Fixed" in output or "issue(s)" in output):
            # This is a format operation - parse for better messaging
            # Prefer standardized counters if present in the output object
            fixed_count: int | None = (
                cast(int | None, getattr(output, "fixed_issues_count", None))
                if hasattr(output, "fixed_issues_count")
                else None
            )
            remaining_count: int | None = (
                cast(
                    int | None,
                    getattr(output, "remaining_issues_count", None),
                )
                if hasattr(output, "remaining_issues_count")
                else None
            )
            initial_count: int | None = (
                cast(int | None, getattr(output, "initial_issues_count", None))
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
                success_func(message=f"✓ {fixed_count} fixed")
            elif fixed_count > 0 and remaining_count > 0:
                console_output_func(
                    text=f"✓ {fixed_count} fixed",
                    color="green",
                )
                console_output_func(
                    text=f"✗ {remaining_count} remaining",
                    color="red",
                )
            elif remaining_count > 0:
                console_output_func(
                    text=f"✗ {remaining_count} remaining",
                    color="red",
                )
            elif initial_count > 0:
                # If we found initial issues but no specific fixed/remaining counts,
                # show the initial count as found
                console_output_func(
                    text=f"✗ Found {initial_count} issues",
                    color="red",
                )
            else:
                # Fallback to original behavior
                error_msg = f"✗ Found {issues_count} issues"
                console_output_func(text=error_msg, color="red")
        else:
            # Show issue count with action-aware phrasing
            if action == Action.FIX:
                error_msg = f"✗ {issues_count} issue(s) cannot be auto-fixed"
            else:
                error_msg = f"✗ Found {issues_count} issues"
            console_output_func(text=error_msg, color="red")

            # Check if there are fixable issues and show warning
            raw_text = (
                raw_output_for_meta if raw_output_for_meta is not None else output
            )
            # Sum all fixable counts if multiple sections are present
            if raw_text and action != Action.FIX:
                # Sum any reported fixable lint issues
                matches = re.findall(r"\[\*\]\s+(\d+)\s+fixable", raw_text)
                fixable_count: int = sum(int(m) for m in matches) if matches else 0
                # Add formatting issues as fixable by fmt when ruff reports them
                if tool_name == ToolName.RUFF and (
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
                    console_output_func(
                        text=hint_a + hint_b + hint_c,
                        color="yellow",
                    )

    # Remove redundant tip; consolidated above as a single auto-fix message

    console_output_func(text="")  # Blank line after each tool
