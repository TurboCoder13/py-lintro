"""Bandit output parser for security issues."""

from typing import Any

from loguru import logger

from lintro.parsers.bandit.bandit_issue import BanditIssue


def parse_bandit_output(bandit_data: dict[str, Any]) -> list[BanditIssue]:
    """Parse Bandit JSON output into BanditIssue objects.

    Args:
        bandit_data: dict[str, Any]: JSON data from Bandit output.

    Returns:
        list[BanditIssue]: List of parsed security issues.

    Raises:
        ValueError: If the bandit data structure is invalid.
    """
    if not isinstance(bandit_data, dict):
        raise ValueError("Bandit data must be a dictionary")

    results = bandit_data.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Bandit results must be a list")

    issues: list[BanditIssue] = []

    for result in results:
        if not isinstance(result, dict):
            continue

        try:
            filename = result.get("filename", "")
            line_number = result.get("line_number", 0)
            col_offset = result.get("col_offset", 0)
            issue_severity = result.get("issue_severity", "UNKNOWN")
            issue_confidence = result.get("issue_confidence", "UNKNOWN")
            test_id = result.get("test_id", "")
            test_name = result.get("test_name", "")
            issue_text = result.get("issue_text", "")
            more_info = result.get("more_info", "")
            cwe = result.get("issue_cwe")
            code = result.get("code")
            line_range = result.get("line_range")

            # Validate critical fields; skip malformed entries
            if not isinstance(filename, str):
                logger.warning("Skipping issue with non-string filename")
                continue
            if not isinstance(line_number, int):
                logger.warning("Skipping issue with non-integer line_number")
                continue
            if not isinstance(col_offset, int):
                col_offset = 0

            sev = (
                str(issue_severity).upper() if issue_severity is not None else "UNKNOWN"
            )
            conf = (
                str(issue_confidence).upper()
                if issue_confidence is not None
                else "UNKNOWN"
            )

            test_id = test_id if isinstance(test_id, str) else ""
            test_name = test_name if isinstance(test_name, str) else ""
            issue_text = issue_text if isinstance(issue_text, str) else ""
            more_info = more_info if isinstance(more_info, str) else ""

            # Normalize line_range to list[int] when provided
            if isinstance(line_range, list):
                line_range = [x for x in line_range if isinstance(x, int)] or None
            else:
                line_range = None

            issue = BanditIssue(
                file=filename,
                line=line_number,
                col_offset=col_offset,
                issue_severity=sev,
                issue_confidence=conf,
                test_id=test_id,
                test_name=test_name,
                issue_text=issue_text,
                more_info=more_info,
                cwe=cwe if isinstance(cwe, dict) else None,
                code=code if isinstance(code, str) else None,
                line_range=line_range,
            )
            issues.append(issue)
        except (KeyError, TypeError, ValueError) as e:
            # Log warning but continue processing other issues
            logger.warning(f"Failed to parse bandit issue: {e}")
            continue

    return issues
