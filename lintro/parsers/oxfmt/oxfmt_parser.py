"""Parser for oxfmt output.

Handles oxfmt CLI output in --list-different mode which outputs
one file path per line for files that need formatting.
"""

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.oxfmt.oxfmt_issue import OxfmtIssue


def parse_oxfmt_output(output: str) -> list[OxfmtIssue]:
    """Parse oxfmt output into a list of OxfmtIssue objects.

    Args:
        output: The raw output from oxfmt --list-different.

    Returns:
        List of OxfmtIssue objects for each file needing formatting.
    """
    issues: list[OxfmtIssue] = []

    if not output:
        return issues

    # Normalize output by stripping ANSI escape sequences
    normalized_output = strip_ansi_codes(output)

    for line in normalized_output.splitlines():
        try:
            line = line.strip()
            if not line:
                continue

            # Each non-empty line is a file path that needs formatting
            issues.append(
                OxfmtIssue(
                    file=line,
                    line=1,
                    column=1,
                    message="File is not formatted",
                    code="FORMAT",
                ),
            )
        except (AttributeError, TypeError) as e:
            logger.debug(f"Failed to parse oxfmt line '{line}': {e}")
            continue

    return issues
