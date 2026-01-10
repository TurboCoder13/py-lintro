"""Parser for darglint output."""

import re

from lintro.parsers.base_parser import collect_continuation_lines
from lintro.parsers.darglint.darglint_issue import DarglintIssue


def _is_darglint_continuation(line: str) -> bool:
    """Check if a line is a continuation of a darglint message.

    Args:
        line: The line to check.

    Returns:
        True if the line is a continuation (indented or colon-prefixed).
    """
    return line.strip().startswith(":") or line.startswith("    ")


def parse_darglint_output(output: str) -> list[DarglintIssue]:
    """Parse darglint output into a list of DarglintIssue objects.

    Args:
        output: The raw output from darglint

    Returns:
        List of DarglintIssue objects
    """
    issues: list[DarglintIssue] = []
    # Patterns:
    # 1. filename:function:line: CODE message
    # 2. filename:line: CODE message (for module-level errors)
    # Accept both "CODE message" and "CODE: message" variants from darglint
    pattern: re.Pattern[str] = re.compile(r"^(.*?):(.*?):(\d+): (D[A-Z]*\d+):? (.*)$")
    alt_pattern: re.Pattern[str] = re.compile(r"^(.*?):(\d+): (D[A-Z]*\d+):? (.*)$")
    lines: list[str] = output.splitlines()
    i: int = 0
    while i < len(lines):
        line: str = lines[i]
        match: re.Match[str] | None = pattern.match(line)
        if match:
            file: str
            line_num: str
            code: str
            message: str
            file, _, line_num, code, message = match.groups()
        else:
            match = alt_pattern.match(line)
            if match:
                file, line_num, code, message = match.groups()
            else:
                i += 1
                continue

        # Capture continuation lines using the shared utility
        continuation, next_idx = collect_continuation_lines(
            lines,
            i + 1,
            _is_darglint_continuation,
        )
        full_message = f"{message} {continuation}".strip() if continuation else message

        issues.append(
            DarglintIssue(
                file=file,
                line=int(line_num),
                code=code,
                message=full_message,
            ),
        )
        i = next_idx
    return issues
