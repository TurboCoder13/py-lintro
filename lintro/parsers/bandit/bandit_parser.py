"""Bandit output parser for security issues."""

from typing import Any

from loguru import logger

from lintro.parsers.bandit.bandit_issue import BanditIssue
from lintro.parsers.base_parser import validate_int_field, validate_str_field


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
            filename = validate_str_field(
                result.get("filename"),
                "filename",
                log_warning=True,
            )
            line_number_raw = result.get("line_number")
            # Skip if line_number is missing or invalid (required field)
            # bool is a subclass of int, so we check for bool first
            if isinstance(line_number_raw, bool):
                logger.warning("Skipping issue with non-integer line_number")
                continue
            if not isinstance(line_number_raw, int):
                logger.warning("Skipping issue with non-integer line_number")
                continue
            # After the isinstance checks above, mypy knows line_number_raw is int
            line_number: int = line_number_raw

            # Skip if filename is empty (required field)
            if not filename:
                logger.warning("Skipping issue with empty filename")
                continue

            col_offset = validate_int_field(result.get("col_offset"), "col_offset")
            issue_severity = result.get("issue_severity", "UNKNOWN")
            issue_confidence = result.get("issue_confidence", "UNKNOWN")
            cwe = result.get("issue_cwe")
            code = result.get("code")
            line_range = result.get("line_range")

            sev = (
                str(issue_severity).upper() if issue_severity is not None else "UNKNOWN"
            )
            conf = (
                str(issue_confidence).upper()
                if issue_confidence is not None
                else "UNKNOWN"
            )

            test_id = validate_str_field(result.get("test_id"), "test_id")
            test_name = validate_str_field(result.get("test_name"), "test_name")
            issue_text = validate_str_field(result.get("issue_text"), "issue_text")
            more_info = validate_str_field(result.get("more_info"), "more_info")

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
                code_snippet=code if isinstance(code, str) else None,
                line_range=line_range,
            )
            issues.append(issue)
        except (KeyError, TypeError, ValueError) as e:
            # Log warning but continue processing other issues
            logger.warning(f"Failed to parse bandit issue: {e}")
            continue

    return issues
