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

            # Collect continuation lines (lines that start with whitespace)
            # These are part of the multi-line message
            i += 1
            continuation_lines: list[str] = []
            while i < len(lines):
                next_line = lines[i]
                # Continuation lines start with whitespace (indentation)
                # Empty lines break the continuation
                if not next_line.strip():
                    break
                if next_line[0].isspace():
                    continuation_lines.append(next_line.strip())
                    i += 1
                else:
                    # Next line doesn't start with whitespace, stop collecting
                    break

            # Combine main message with continuation lines
            full_message = message.strip()
            if continuation_lines:
                full_message = " ".join([full_message] + continuation_lines)

            issues.append(
                MarkdownlintIssue(
                    file=filename,
                    line=int(line_num),
                    column=int(column) if column else None,
                    code=code,
                    message=full_message,
                ),
            )
        else:
            # Line doesn't match pattern, skip it
            i += 1

    return issues
