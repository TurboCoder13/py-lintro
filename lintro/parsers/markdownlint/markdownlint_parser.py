"""Parser for markdownlint-cli2 output."""

import re

from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue


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

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip metadata lines (version, Finding, Linting, Summary)
        if (
            line.startswith("markdownlint-cli2")
            or line.startswith("Finding:")
            or line.startswith("Linting:")
            or line.startswith("Summary:")
        ):
            continue

        # Pattern for markdownlint-cli2 default formatter:
        # file:line[:column] error MD###/rule-name Message [Context: "..."]
        # Column is optional, and Context is optional
        # Also handles variations like: file:line error MD### Message
        # [Expected: ...; Actual: ...]
        pattern: re.Pattern[str] = re.compile(
            r"^([^:]+):(\d+)(?::(\d+))?\s+error\s+(MD\d+)(?:/[^:\s]+)?(?::\s*)?"
            r"(.+?)(?:\s+\[(?:Context|Expected|Actual):.*?\])?$",
        )

        match: re.Match[str] | None = pattern.match(line)
        if match:
            filename: str
            line_num: str
            column: str | None
            code: str
            message: str
            filename, line_num, column, code, message = match.groups()

            issues.append(
                MarkdownlintIssue(
                    file=filename,
                    line=int(line_num),
                    column=int(column) if column else None,
                    code=code,
                    message=message.strip(),
                ),
            )

    return issues
