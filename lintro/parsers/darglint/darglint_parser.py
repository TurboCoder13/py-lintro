"""Parser for darglint output."""

import re

from lintro.parsers.darglint.darglint_issue import DarglintIssue


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
            obj: str
            line_num: str
            code: str
            message: str
            file, obj, line_num, code, message = match.groups()
        else:
            match = alt_pattern.match(line)
            if match:
                file, line_num, code, message = match.groups()
            else:
                i += 1
                continue
        # Capture all subsequent indented or colon-prefixed lines as part of the message
        message_lines: list[str] = [message]
        j: int = i + 1
        while j < len(lines) and (
            lines[j].strip().startswith(":") or lines[j].startswith("    ")
        ):
            # Remove leading colon and whitespace
            message_lines.append(lines[j].strip().lstrip(": "))
            j += 1
        full_message: str = " ".join(message_lines)
        issues.append(
            DarglintIssue(
                file=file,
                line=int(line_num),
                code=code,
                message=full_message,
            )
        )
        i = j
    return issues
