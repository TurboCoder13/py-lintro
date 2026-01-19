"""Parser for taplo output.

This module provides parsing functionality for taplo TOML linter/formatter
text output format.
"""

from __future__ import annotations

import re

from lintro.parsers.taplo.taplo_issue import TaploIssue


def parse_taplo_output(output: str | None) -> list[TaploIssue]:
    """Parse taplo output into a list of TaploIssue objects.

    Taplo outputs errors in the format:
    error[code]: message
      --> file:line:column
       |
     N | code line content
       |          ^ error indicator

    Example output:
    error[invalid_value]: invalid value
      --> pyproject.toml:5:10
       |
     5 | version =
       |          ^ expected a value

    Args:
        output: The raw output from taplo, or None.

    Returns:
        List of TaploIssue objects parsed from the output.
    """
    issues: list[TaploIssue] = []

    # Handle None or empty output
    if not output or not output.strip():
        return issues

    # Pattern for taplo error header: error[code]: message or warning[code]: message
    header_pattern: re.Pattern[str] = re.compile(
        r"^(error|warning)\[([^\]]+)\]:\s*(.+)$",
    )

    # Pattern for location line:   --> file:line:column
    location_pattern: re.Pattern[str] = re.compile(
        r"^\s*-->\s*(.+):(\d+):(\d+)\s*$",
    )

    # Pattern for taplo fmt --check output:
    # ERROR taplo:format_files: the file is not properly formatted path="..."
    fmt_check_pattern: re.Pattern[str] = re.compile(
        r'^ERROR\s+taplo:format_files:\s*(.+?)\s+path="([^"]+)"',
    )

    lines: list[str] = output.splitlines()
    i: int = 0

    while i < len(lines):
        line: str = lines[i]

        # Try to match taplo fmt --check output first
        fmt_match: re.Match[str] | None = fmt_check_pattern.match(line)
        if fmt_match:
            message: str = fmt_match.group(1).strip()
            file_path: str = fmt_match.group(2)
            issues.append(
                TaploIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    level="error",
                    code="format",
                    message=message,
                ),
            )
            i += 1
            continue

        # Try to match error/warning header
        header_match: re.Match[str] | None = header_pattern.match(line)
        if header_match:
            level: str = header_match.group(1)
            code: str = header_match.group(2)
            message = header_match.group(3).strip()

            # Look for location in next lines
            file_path = ""
            line_num: int = 0
            column: int = 0

            # Search ahead for the location line (usually within 1-2 lines)
            for j in range(i + 1, min(i + 5, len(lines))):
                location_match: re.Match[str] | None = location_pattern.match(lines[j])
                if location_match:
                    file_path = location_match.group(1)
                    line_num = int(location_match.group(2))
                    column = int(location_match.group(3))
                    break

            issues.append(
                TaploIssue(
                    file=file_path,
                    line=line_num,
                    column=column,
                    level=level,
                    code=code,
                    message=message,
                ),
            )

        i += 1

    return issues
