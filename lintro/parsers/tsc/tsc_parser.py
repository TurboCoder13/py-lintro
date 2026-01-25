"""Parser for tsc (TypeScript Compiler) text output."""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.tsc.tsc_issue import TscIssue

# Pattern for tsc output with --pretty false:
# file.ts(line,col): error TS1234: message
# file.ts(line,col): warning TS1234: message
# Also handles Windows paths with backslashes
TSC_ISSUE_PATTERN = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*"
    r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*"
    r"(?P<message>.+)$",
)


def _parse_line(line: str) -> TscIssue | None:
    """Parse a single tsc output line into a TscIssue.

    Args:
        line: A single line of tsc output.

    Returns:
        A TscIssue instance or None if the line doesn't match the expected format.
    """
    line = line.strip()
    if not line:
        return None

    match = TSC_ISSUE_PATTERN.match(line)
    if not match:
        return None

    try:
        file_path = match.group("file")
        line_num = int(match.group("line"))
        column = int(match.group("column"))
        severity = match.group("severity")
        code = match.group("code")
        message = match.group("message").strip()

        # Normalize Windows paths to forward slashes
        file_path = file_path.replace("\\", "/")

        return TscIssue(
            file=file_path,
            line=line_num,
            column=column,
            code=code,
            message=message,
            severity=severity,
        )
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse tsc line: {e}")
        return None


def parse_tsc_output(output: str) -> list[TscIssue]:
    """Parse tsc text output into TscIssue objects.

    Args:
        output: Raw stdout emitted by tsc with --pretty false.

    Returns:
        A list of TscIssue instances parsed from the output. Returns an
        empty list when no issues are present or the output cannot be decoded.

    Examples:
        >>> output = "src/main.ts(10,5): error TS2322: Type error."
        >>> issues = parse_tsc_output(output)
        >>> len(issues)
        1
        >>> issues[0].code
        'TS2322'
    """
    if not output or not output.strip():
        return []

    issues: list[TscIssue] = []
    for line in output.splitlines():
        parsed = _parse_line(line)
        if parsed:
            issues.append(parsed)

    return issues
