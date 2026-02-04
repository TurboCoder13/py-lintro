"""Parser for hadolint output."""

import re

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.hadolint.hadolint_issue import HadolintIssue


def parse_hadolint_output(output: str) -> list[HadolintIssue]:
    """Parse hadolint output into a list of HadolintIssue objects.

    Hadolint outputs in the format:
    filename:line code level: message

    Example outputs:
    Dockerfile:1 DL3006 error: Always tag the version of an image explicitly
    Dockerfile:3 DL3009 warning: Delete the apt-get lists after installing
        something
    Dockerfile:5 DL3015 info: Avoid additional packages by specifying
        `--no-install-recommends`

    Args:
        output: The raw output from hadolint

    Returns:
        List of HadolintIssue objects
    """
    issues: list[HadolintIssue] = []

    # Skip empty output
    if not output.strip():
        return issues

    # Strip ANSI codes for consistent parsing across environments
    output = strip_ansi_codes(output)

    # Pattern for hadolint output: filename:line code level: message
    pattern: re.Pattern[str] = re.compile(
        r"^(.+?):(\d+)\s+([A-Z]+\d+)\s+(error|warning|info|style):\s+(.+)$",
    )

    lines: list[str] = output.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match: re.Match[str] | None = pattern.match(line)
        if match:
            file: str
            line_num: str
            code: str
            level: str
            message: str
            file, line_num, code, level, message = match.groups()

            issues.append(
                HadolintIssue(
                    file=file,
                    line=int(line_num),
                    column=0,  # hadolint doesn't provide column in this format
                    level=level,
                    code=code,
                    message=message.strip(),
                ),
            )

    return issues
