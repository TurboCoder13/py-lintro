"""Parser for ruff output (lint and format).

This module provides functions to parse both:
- ruff check --output-format json (linting issues)
- ruff format --check (plain text: files needing formatting)
"""

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
        # Ruff outputs JSON array of issue objects, but may have warnings
        # after. Find the end of the JSON array by looking for the
        # closing
        # bracket
        json_end = output.rfind("]")
        if json_end == -1:
            # No closing bracket found, try to parse the whole output
            ruff_data = json.loads(output)
        else:
            # Extract just the JSON part (up to and including the closing bracket)
            json_part = output[: json_end + 1]
            ruff_data = json.loads(json_part)

        for item in ruff_data:
            # Extract fix applicability if available
            fix_applicability = None
            if item.get("fix"):
                fix_applicability = item["fix"].get("applicability")

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
                    fix_applicability=fix_applicability,
                )
            )
    except (json.JSONDecodeError, KeyError, TypeError):
        # If JSON parsing fails, return empty list
        # Could also log the error for debugging
        pass

    return issues


def parse_ruff_format_check_output(output: str) -> list[str]:
    """Parse the output of `ruff format --check` to get files needing formatting.

    Args:
        output: The raw output from `ruff format --check`

    Returns:
        List of file paths that would be reformatted
    """
    if not output:
        return []
    files = []
    for line in output.splitlines():
        line = line.strip()
        # Ruff format --check output: 'Would reformat: path/to/file.py' or
        # 'Would reformat path/to/file.py'
        if line.startswith("Would reformat: "):
            files.append(line[len("Would reformat: ") :])
        elif line.startswith("Would reformat "):
            files.append(line[len("Would reformat ") :])
    return files
