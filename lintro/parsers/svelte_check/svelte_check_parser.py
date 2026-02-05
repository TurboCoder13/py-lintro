"""Parser for svelte-check --output machine-verbose output."""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.svelte_check.svelte_check_issue import SvelteCheckIssue

# Pattern for svelte-check machine-verbose output:
# <file>:<startLine>:<startCol>:<endLine>:<endCol> <severity> <message>
# Example: src/lib/Button.svelte:15:5:15:10 Error Type 'string' is not assignable
MACHINE_VERBOSE_PATTERN = re.compile(
    r"^(?P<file>.+?):"
    r"(?P<start_line>\d+):"
    r"(?P<start_col>\d+):"
    r"(?P<end_line>\d+):"
    r"(?P<end_col>\d+)\s+"
    r"(?P<severity>Error|Warning|Hint)\s+"
    r"(?P<message>.+)$",
)

# Alternative pattern for simpler format (machine output without verbose):
# <severity> <file>:<line>:<col> <message>
MACHINE_PATTERN = re.compile(
    r"^(?P<severity>ERROR|WARN|HINT)\s+"
    r"(?P<file>.+?):"
    r"(?P<line>\d+):"
    r"(?P<col>\d+)\s+"
    r"(?P<message>.+)$",
    re.IGNORECASE,
)

# Pattern for human-readable format as fallback:
# file.svelte:line:col
#   severity: message
HUMAN_FILE_PATTERN = re.compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+)$")


def _normalize_severity(severity: str) -> str:
    """Normalize severity string to lowercase standard form.

    Args:
        severity: Raw severity string from output.

    Returns:
        Normalized severity ("error", "warning", or "hint").
    """
    severity_lower = severity.lower()
    if severity_lower in ("error", "err"):
        return "error"
    if severity_lower in ("warning", "warn"):
        return "warning"
    if severity_lower == "hint":
        return "hint"
    return "error"  # Default to error for unknown


def _parse_machine_verbose_line(line: str) -> SvelteCheckIssue | None:
    """Parse a machine-verbose format line.

    Args:
        line: A single line of svelte-check output.

    Returns:
        A SvelteCheckIssue instance or None if the line doesn't match.
    """
    match = MACHINE_VERBOSE_PATTERN.match(line)
    if not match:
        return None

    try:
        file_path = match.group("file").replace("\\", "/")
        start_line = int(match.group("start_line"))
        start_col = int(match.group("start_col"))
        end_line = int(match.group("end_line"))
        end_col = int(match.group("end_col"))
        severity = _normalize_severity(match.group("severity"))
        message = match.group("message").strip()

        return SvelteCheckIssue(
            file=file_path,
            line=start_line,
            column=start_col,
            end_line=end_line if end_line != start_line else None,
            end_column=end_col if end_col != start_col else None,
            severity=severity,
            message=message,
        )
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse svelte-check machine-verbose line: {e}")
        return None


def _parse_machine_line(line: str) -> SvelteCheckIssue | None:
    """Parse a machine format line (simpler format).

    Args:
        line: A single line of svelte-check output.

    Returns:
        A SvelteCheckIssue instance or None if the line doesn't match.
    """
    match = MACHINE_PATTERN.match(line)
    if not match:
        return None

    try:
        file_path = match.group("file").replace("\\", "/")
        line_num = int(match.group("line"))
        column = int(match.group("col"))
        severity = _normalize_severity(match.group("severity"))
        message = match.group("message").strip()

        return SvelteCheckIssue(
            file=file_path,
            line=line_num,
            column=column,
            severity=severity,
            message=message,
        )
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse svelte-check machine line: {e}")
        return None


def _parse_line(line: str) -> SvelteCheckIssue | None:
    """Parse a single svelte-check output line into a SvelteCheckIssue.

    Args:
        line: A single line of svelte-check output.

    Returns:
        A SvelteCheckIssue instance or None if the line doesn't match.
    """
    line = line.strip()
    if not line:
        return None

    # Skip summary lines and noise
    if line.startswith(("=====", "svelte-check", "Loading", "Diagnostics")):
        return None

    # Try machine-verbose format first
    issue = _parse_machine_verbose_line(line)
    if issue:
        return issue

    # Try machine format
    issue = _parse_machine_line(line)
    if issue:
        return issue

    return None


def parse_svelte_check_output(output: str) -> list[SvelteCheckIssue]:
    """Parse svelte-check output into SvelteCheckIssue objects.

    Args:
        output: Raw stdout emitted by svelte-check --output machine-verbose.

    Returns:
        A list of SvelteCheckIssue instances parsed from the output.

    Examples:
        >>> output = "src/lib/Button.svelte:15:5:15:10 Error Type error"
        >>> issues = parse_svelte_check_output(output)
        >>> len(issues)
        1
    """
    if not output or not output.strip():
        return []

    # Strip ANSI codes for consistent parsing
    output = strip_ansi_codes(output)

    issues: list[SvelteCheckIssue] = []
    for line in output.splitlines():
        parsed = _parse_line(line)
        if parsed:
            issues.append(parsed)

    return issues
