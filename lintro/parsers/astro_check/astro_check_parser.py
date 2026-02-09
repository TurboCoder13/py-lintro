"""Parser for astro check output."""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.astro_check.astro_check_issue import AstroCheckIssue
from lintro.parsers.base_parser import strip_ansi_codes

# Pattern for astro check output:
# file.astro:line:col - severity ts1234: message
# Also handles tsc-style output: file.astro(line,col): error TS1234: message
ASTRO_ISSUE_PATTERN = re.compile(
    r"^(?P<file>.+?)"
    r"(?:"
    r"\((?P<line_paren>\d+),(?P<col_paren>\d+)\)"  # tsc style: file(line,col)
    r"|"
    r":(?P<line_colon>\d+):(?P<col_colon>\d+)"  # astro style: file:line:col
    r")"
    r"(?:\s*[-:]\s*|\s+)"
    r"(?P<severity>error|warning|hint)?\s*"
    r"(?:(?P<code>ts\d+|TS\d+)[:\s]+)?"
    r"(?P<message>.+)$",
    re.IGNORECASE,
)

# Alternative pattern for simpler format:
# src/pages/index.astro:5:3 Type 'X' is not assignable to type 'Y'.
ASTRO_SIMPLE_PATTERN = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+)\s+(?P<message>.+)$",
)

# Astro-check stderr timestamp prefix: HH:MM:SS
# e.g. "15:19:56 [content] Syncing content"
# These must be filtered before regex matching because the HH:MM:SS format
# is indistinguishable from a file:line:col triplet.
_TIMESTAMP_PREFIX = re.compile(r"^\d{1,2}:\d{2}:\d{2}\s")


def _parse_line(line: str) -> AstroCheckIssue | None:
    """Parse a single astro check output line into an AstroCheckIssue.

    Args:
        line: A single line of astro check output.

    Returns:
        An AstroCheckIssue instance or None if the line doesn't match.
    """
    line = line.strip()
    if not line:
        return None

    # Skip summary lines and noise
    if line.startswith(("Result", "Found", "Checking", "...")):
        return None

    # Skip astro-check stderr timestamp lines (HH:MM:SS prefix).
    # These are informational log messages like:
    #   15:19:56 [WARN] Missing pages directory: src/pages
    #   15:19:56 [content] Syncing content
    # Without this filter the HH:MM:SS prefix is misinterpreted as
    # file:line:col by the fallback ASTRO_SIMPLE_PATTERN.
    if _TIMESTAMP_PREFIX.match(line):
        return None

    match = ASTRO_ISSUE_PATTERN.match(line)
    if match:
        try:
            file_path = match.group("file")
            # Handle both tsc-style and astro-style line/col
            line_paren = match.group("line_paren")
            line_colon = match.group("line_colon")
            col_paren = match.group("col_paren")
            col_colon = match.group("col_colon")

            # Warn if neither line format matched (unexpected regex state)
            if line_paren is None and line_colon is None:
                logger.warning(
                    "[astro-check] Regex matched but no line number found: %s",
                    line,
                )
                return None

            line_num = int(line_paren or line_colon)
            column = int(col_paren or col_colon or "1")  # Default col to 1 if missing

            severity = match.group("severity")
            code = match.group("code")
            message = match.group("message").strip()

            # Normalize Windows paths to forward slashes
            file_path = file_path.replace("\\", "/")

            # Normalize code to uppercase
            if code:
                code = code.upper()

            return AstroCheckIssue(
                file=file_path,
                line=line_num,
                column=column,
                code=code or "",
                message=message,
                severity=severity.lower() if severity else "error",
            )
        except (ValueError, AttributeError) as e:
            logger.debug(
                "[astro-check] Failed to parse line with main pattern: {}",
                e,
            )

    # Try simpler pattern as fallback
    match = ASTRO_SIMPLE_PATTERN.match(line)
    if match:
        try:
            return AstroCheckIssue(
                file=match.group("file").replace("\\", "/"),
                line=int(match.group("line")),
                column=int(match.group("col")),
                message=match.group("message").strip(),
                severity="error",
            )
        except (ValueError, AttributeError) as e:
            logger.debug(
                "[astro-check] Failed to parse line with simple pattern: {}",
                e,
            )

    return None


def parse_astro_check_output(output: str) -> list[AstroCheckIssue]:
    """Parse astro check output into AstroCheckIssue objects.

    Args:
        output: Raw stdout emitted by astro check.

    Returns:
        A list of AstroCheckIssue instances parsed from the output.

    Examples:
        >>> output = "src/pages/index.astro:10:5 - error ts2322: Type error."
        >>> issues = parse_astro_check_output(output)
        >>> len(issues)
        1
    """
    if not output or not output.strip():
        return []

    # Strip ANSI codes for consistent parsing
    output = strip_ansi_codes(output)

    issues: list[AstroCheckIssue] = []
    for line in output.splitlines():
        parsed = _parse_line(line)
        if parsed:
            issues.append(parsed)

    return issues
