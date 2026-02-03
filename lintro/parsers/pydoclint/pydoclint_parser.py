"""Parser for pydoclint output.

This module provides parsing functionality for pydoclint's text output format.
Pydoclint is a Python docstring linter that validates docstrings match
function signatures.
"""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.pydoclint.pydoclint_issue import PydoclintIssue

# Pydoclint output format:
#   /path/to/file.py
#       10: DOC101: Function `foo` has 1 argument(s) ...
# File path is on its own line, issues start with whitespace then line number
PYDOCLINT_FILE_PATTERN = re.compile(r"^(?P<file>\S.*\.pyi?)$")
PYDOCLINT_ISSUE_PATTERN = re.compile(
    r"^\s+(?P<line>\d+):\s*(?P<code>DOC\d+):\s*(?P<message>.+)$",
)


def _safe_int(value: str, default: int = 0) -> int:
    """Safely convert a value to int with fallback.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Integer value or default.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_pydoclint_output(output: str | None) -> list[PydoclintIssue]:
    """Parse pydoclint text output into a list of PydoclintIssue objects.

    Pydoclint outputs text in the following format:
    /path/to/file.py
        10: DOC101: Function `foo` has 1 argument(s) ...

    The file path is on its own line, followed by indented issue lines.

    Args:
        output: The raw text output from pydoclint, or None.

    Returns:
        List of PydoclintIssue objects.
    """
    issues: list[PydoclintIssue] = []

    # Handle None or empty output
    if output is None or not output.strip():
        return issues

    # Strip ANSI codes for consistent parsing across environments
    output = strip_ansi_codes(output)

    current_file: str | None = None

    for line in output.splitlines():
        # Skip empty lines
        if not line.strip():
            continue

        # Check if this is a file path line (no leading whitespace)
        file_match = PYDOCLINT_FILE_PATTERN.match(line)
        if file_match:
            current_file = file_match.group("file")
            logger.debug(f"Parsing issues for file: {current_file}")
            continue

        # Check if this is an issue line (has leading whitespace)
        issue_match = PYDOCLINT_ISSUE_PATTERN.match(line)
        if issue_match:
            if current_file:
                line_num = _safe_int(issue_match.group("line"))
                code = issue_match.group("code")
                message = issue_match.group("message")

                issues.append(
                    PydoclintIssue(
                        file=current_file,
                        line=line_num,
                        column=0,  # pydoclint doesn't provide column info
                        code=code,
                        message=message,
                    ),
                )
            else:
                # Issue found but no file context - log for debugging
                logger.warning(
                    f"Pydoclint issue found without file context: "
                    f"line={issue_match.group('line')}, "
                    f"code={issue_match.group('code')}, "
                    f"message={issue_match.group('message')}",
                )
        else:
            logger.debug(f"Line did not match pydoclint pattern: {line}")

    return issues
