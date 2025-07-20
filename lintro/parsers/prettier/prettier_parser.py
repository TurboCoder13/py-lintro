"""Parser for Prettier output."""

import re
from typing import List

from lintro.parsers.prettier.prettier_issue import PrettierIssue


def _strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text.

    Args:
        text: Text that may contain ANSI escape sequences.

    Returns:
        Text with ANSI codes removed.
    """
    # ANSI escape sequence pattern: \x1b[...m
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def parse_prettier_output(output: str) -> List[PrettierIssue]:
    """Parse Prettier output into a list of Issue objects.

    Args:
        output: The raw output from Prettier.

    Returns:
        List[PrettierIssue]: List of Issue objects parsed from output.
    """
    issues = []
    # Strip ANSI color codes from the entire output first
    clean_output = _strip_ansi_codes(output)

    # Prettier output: [warn] file.js 123ms or [warn]    file.js
    pattern = re.compile(r"\[warn\]\s+(.*?)(?:\s+\d+ms)?$")
    for line in clean_output.splitlines():
        match = pattern.match(line.strip())
        if match:
            file_path = match.group(1).strip()
            if file_path and not file_path.startswith("Code style issues found"):
                issues.append(
                    PrettierIssue(
                        file=file_path,
                        line=None,
                        code="PRETTIER",
                        message="File needs formatting",
                    )
                )
    return issues
