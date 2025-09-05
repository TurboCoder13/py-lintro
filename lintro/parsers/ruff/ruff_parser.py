"""Parser for ruff output (lint and format).

This module provides functions to parse both:
- ruff check --output-format json (linting issues)
- ruff format --check (plain text: files needing formatting)
"""

import json

from lintro.parsers.ruff.ruff_issue import RuffIssue


def parse_ruff_output(output: str) -> list[RuffIssue]:
    """Parse Ruff JSON or JSON Lines output into `RuffIssue` objects.

    Supports multiple Ruff schema variants across versions by accepting:
    - JSON array of issue objects
    - JSON Lines (one object per line)

    Field name variations handled:
    - location: "location" or "start" with keys "row"|"line" and
      "column"|"col"
    - end location: "end_location" or "end" with keys "row"|"line" and
      "column"|"col"
    - filename: "filename" (preferred) or "file"

    Args:
        output: Raw output from `ruff check --output-format json`.

    Returns:
        list[RuffIssue]: Parsed issues.
    """
    issues: list[RuffIssue] = []

    if not output or output.strip() in ("[]", "{}"):
        return issues

    def _int_from(d: dict, candidates: list[str]) -> int | None:
        for key in candidates:
            val = d.get(key)
            if isinstance(val, int):
                return val
        return None

    def _parse_item(item: dict) -> RuffIssue | None:
        try:
            filename: str = item.get("filename") or item.get("file") or ""

            loc: dict = item.get("location") or item.get("start") or {}
            end_loc: dict = item.get("end_location") or item.get("end") or {}

            line = _int_from(loc, ["row", "line"]) or 0
            column = _int_from(loc, ["column", "col"]) or 0
            end_line = _int_from(end_loc, ["row", "line"]) or line
            end_column = _int_from(end_loc, ["column", "col"]) or column

            code: str = item.get("code") or item.get("rule") or ""
            message: str = item.get("message") or ""
            url: str | None = item.get("url")

            fix = item.get("fix") or {}
            fixable: bool = bool(fix)
            fix_applicability = (
                fix.get("applicability") if isinstance(fix, dict) else None
            )

            return RuffIssue(
                file=filename,
                line=line,
                column=column,
                code=code,
                message=message,
                url=url,
                end_line=end_line,
                end_column=end_column,
                fixable=fixable,
                fix_applicability=fix_applicability,
            )
        except Exception:
            return None

    # First try JSON array (with possible trailing non-JSON data)
    try:
        json_end = output.rfind("]")
        if json_end != -1:
            json_part = output[: json_end + 1]
            ruff_data = json.loads(json_part)
        else:
            ruff_data = json.loads(output)

        if isinstance(ruff_data, list):
            for item in ruff_data:
                if not isinstance(item, dict):
                    continue
                parsed = _parse_item(item)
                if parsed is not None:
                    issues.append(parsed)
            return issues
    except (json.JSONDecodeError, TypeError):
        # Fall back to JSON Lines parsing below
        pass

    # Fallback: parse JSON Lines (each line is a JSON object)
    for line in output.splitlines():
        line_str = line.strip()
        if not line_str or not line_str.startswith("{"):
            continue
        try:
            item = json.loads(line_str)
            if isinstance(item, dict):
                parsed = _parse_item(item)
                if parsed is not None:
                    issues.append(parsed)
        except json.JSONDecodeError:
            continue

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
