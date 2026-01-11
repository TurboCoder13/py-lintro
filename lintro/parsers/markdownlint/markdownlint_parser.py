"""Parser for markdownlint-cli2 output."""

import re

from lintro.parsers.base_parser import collect_continuation_lines
from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue


def _is_markdownlint_continuation(line: str) -> bool:
    """Check if a line is a continuation of a markdownlint message.

    Continuation lines start with whitespace (indentation) and are non-empty.

    Args:
        line: The line to check.

    Returns:
        True if the line is a continuation (starts with whitespace and non-empty).
    """
    return bool(line.strip()) and line[0].isspace()


def parse_markdownlint_output(output: str) -> list[MarkdownlintIssue]:
    """Parse markdownlint-cli2 output into a list of MarkdownlintIssue objects.

    Markdownlint-cli2 default formatter outputs lines like:
    file:line:column MD###/rule-name Message [Context: "..."]
    or
    file:line MD###/rule-name Message [Context: "..."]

    Example outputs:
    dir/about.md:1:1 MD021/no-multiple-space-closed-atx Multiple spaces
        inside hashes on closed atx style heading [Context: "#  About  #"]
    dir/about.md:4 MD032/blanks-around-lists Lists should be surrounded
        by blank lines [Context: "1. List"]
    viewme.md:3:10 MD009/no-trailing-spaces Trailing spaces
        [Expected: 0 or 2; Actual: 1]

    Args:
        output: The raw output from markdownlint-cli2

    Returns:
        List of MarkdownlintIssue objects
    """
    issues: list[MarkdownlintIssue] = []

    # Skip empty output
    if not output.strip():
        return issues

    lines: list[str] = output.splitlines()

    # Pattern for markdownlint-cli2 default formatter:
    # file:line[:column] [error] MD###/rule-name Message [Context: "..."]
    # Column is optional, "error" keyword is optional, and Context is optional
    # Also handles variations like: file:line MD### Message
    # [Expected: ...; Actual: ...]
    pattern: re.Pattern[str] = re.compile(
        r"^([^:]+):(\d+)(?::(\d+))?\s+(?:error\s+)?(MD\d+)(?:/[^:\s]+)?(?::\s*)?"
        r"(.+?)(?:\s+\[(?:Context|Expected|Actual):.*?\])?$",
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Skip metadata lines (version, Finding, Linting, Summary)
        stripped_line = line.strip()
        if (
            stripped_line.startswith("markdownlint-cli2")
            or stripped_line.startswith("Finding:")
            or stripped_line.startswith("Linting:")
            or stripped_line.startswith("Summary:")
        ):
            i += 1
            continue

        # Try to match the pattern on the current line
        match: re.Match[str] | None = pattern.match(stripped_line)
        if match:
            filename: str
            line_num: str
            column: str | None
            code: str
            message: str
            filename, line_num, column, code, message = match.groups()

            # Collect continuation lines using the shared utility
            continuation, next_idx = collect_continuation_lines(
                lines,
                i + 1,
                _is_markdownlint_continuation,
            )

            # Combine main message with continuation lines
            full_message = message.strip()
            if continuation:
                full_message = f"{full_message} {continuation}"

            issues.append(
                MarkdownlintIssue(
                    file=filename,
                    line=int(line_num),
                    column=int(column) if column else 0,
                    code=code,
                    message=full_message,
                ),
            )
            i = next_idx
        else:
            # Line doesn't match pattern, skip it
            i += 1

    return issues
