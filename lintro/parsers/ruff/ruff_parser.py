"""Parser for ruff output."""

import json
from typing import List

from lintro.parsers.ruff.ruff_issue import RuffIssue


def parse_ruff_output(output: str) -> List[RuffIssue]:
    """Parse ruff JSON output into a list of RuffIssue objects.

    Args:
        output: The raw JSON output from ruff

    Returns:
        List of RuffIssue objects
    """
    issues: List[RuffIssue] = []

    if not output or output.strip() == "[]":
        return issues

    try:
        # Ruff outputs JSON array of issue objects
        ruff_data = json.loads(output)

        for item in ruff_data:
            issues.append(
                RuffIssue(
                    file=item["filename"],
                    line=item["location"]["row"],
                    column=item["location"]["column"],
                    code=item["code"],
                    message=item["message"],
                    url=item.get("url"),
                    end_line=item["end_location"]["row"],
                    end_column=item["end_location"]["column"],
                    fixable=bool(item.get("fix")),
                )
            )
    except (json.JSONDecodeError, KeyError, TypeError):
        # If JSON parsing fails, return empty list
        # Could also log the error for debugging
        pass

    return issues
