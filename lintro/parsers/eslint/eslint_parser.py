"""Parser for ESLint JSON output.

Handles ESLint JSON format output from --format json flag.
"""

import json
from typing import Any

from lintro.parsers.eslint.eslint_issue import EslintIssue


def parse_eslint_output(output: str) -> list[EslintIssue]:
    """Parse ESLint JSON output into a list of EslintIssue objects.

    Args:
        output: The raw JSON output from ESLint.

    Returns:
        List of EslintIssue objects.
    """
    issues: list[EslintIssue] = []

    if not output:
        return issues

    try:
        # ESLint JSON format is an array of file results
        # Each file result has: filePath, messages[], errorCount, warningCount
        eslint_data: list[dict[str, Any]] = json.loads(output)
    except json.JSONDecodeError:
        # If output is not valid JSON, return empty list
        return issues

    for file_result in eslint_data:
        file_path: str = file_result.get("filePath", "")
        messages: list[dict[str, Any]] = file_result.get("messages", [])

        for msg in messages:
            # Extract issue details from ESLint message format
            line: int = msg.get("line", 1)
            column: int = msg.get("column", 1)
            rule_id: str = msg.get("ruleId", "unknown")
            message_text: str = msg.get("message", "")
            severity: int = msg.get("severity", 2)  # Default to error (2)
            fixable: bool = msg.get("fix") is not None  # Has fix object if fixable

            # Skip messages without a ruleId (usually syntax errors)
            if not rule_id:
                continue

            issues.append(
                EslintIssue(
                    file=file_path,
                    line=line,
                    column=column,
                    code=rule_id,
                    message=message_text,
                    severity=severity,
                    fixable=fixable,
                ),
            )

    return issues
