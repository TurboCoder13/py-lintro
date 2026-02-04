"""Parser for yamllint output."""

import re

from loguru import logger

from lintro.enums.severity_level import normalize_severity_level
from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.yamllint.yamllint_issue import YamllintIssue

# Pattern for yamllint parsable format: "filename:line:column: [level] message (rule)"
_YAMLLINT_PATTERN: re.Pattern[str] = re.compile(
    r"^([^:]+):(\d+):(\d+):\s*\[(error|warning)\]\s+(.+?)(?:\s+\(([^)]+)\))?$",
)


def parse_yamllint_output(output: str) -> list[YamllintIssue]:
    """Parse yamllint output into a list of YamllintIssue objects.

    Yamllint outputs in parsable format as:
    filename:line:column: [level] message (rule)

    Example outputs:
    test_samples/yaml_violations.yml:3:1: [warning] missing document start
        "---" (document-start)
    test_samples/yaml_violations.yml:6:32: [error] trailing spaces
        (trailing-spaces)
    test_samples/yaml_violations.yml:11:81: [error] line too long (149 > 80
        characters) (line-length)

    Args:
        output: The raw output from yamllint

    Returns:
        List of YamllintIssue objects
    """
    issues: list[YamllintIssue] = []

    # Skip empty output
    if not output.strip():
        return issues

    # Strip ANSI codes for consistent parsing across environments
    output = strip_ansi_codes(output)

    lines: list[str] = output.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match: re.Match[str] | None = _YAMLLINT_PATTERN.match(line)
        if match:
            try:
                filename: str
                line_num: str
                column: str
                level: str
                message: str
                rule: str | None
                filename, line_num, column, level, message, rule = match.groups()

                # Validate and convert line number
                try:
                    line_int = int(line_num)
                except ValueError:
                    logger.debug(f"Invalid line number in yamllint output: {line_num}")
                    continue

                # Validate and convert column number
                column_int: int = 0
                if column:
                    try:
                        column_int = int(column)
                    except ValueError:
                        logger.debug(
                            f"Invalid column number in yamllint output: {column}",
                        )
                        column_int = 0

                issues.append(
                    YamllintIssue(
                        file=filename,
                        line=line_int,
                        column=column_int,
                        level=normalize_severity_level(level),
                        rule=rule,
                        message=message.strip(),
                    ),
                )
            except (ValueError, TypeError, IndexError) as e:
                logger.debug(f"Failed to parse yamllint line '{line}': {e}")
                continue

    return issues
