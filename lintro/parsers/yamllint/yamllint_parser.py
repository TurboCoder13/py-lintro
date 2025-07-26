"""Parser for yamllint output."""

import re

from lintro.parsers.yamllint.yamllint_issue import YamllintIssue


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

    lines = output.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pattern for yamllint parsable format: "filename:line:column: [level]
        # message (rule)"
        pattern = re.compile(
            r"^([^:]+):(\d+):(\d+):\s*\[(error|warning)\]\s+(.+?)(?:\s+\(([^)]+)\))?$"
        )

        match = pattern.match(line)
        if match:
            filename, line_num, column, level, message, rule = match.groups()

            issues.append(
                YamllintIssue(
                    file=filename,
                    line=int(line_num),
                    column=int(column) if column else None,
                    level=level,
                    rule=rule,
                    message=message.strip(),
                )
            )

    return issues
