"""Parser for pytest output.

This module provides functions to parse pytest output in various formats:
- JSON output from pytest --json-report
- Plain text output from pytest
- JUnit XML output from pytest --junitxml

All parsing functions are re-exported from submodules for backwards compatibility.
"""

from __future__ import annotations

from lintro.enums.pytest_enums import PytestOutputFormat, normalize_pytest_output_format
from lintro.parsers.pytest.format_parsers import (
    _parse_json_test_item,
    parse_pytest_json_output,
    parse_pytest_junit_xml,
    parse_pytest_text_output,
)
from lintro.parsers.pytest.models import PytestSummary
from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.parsers.pytest.summary_extractor import extract_pytest_summary


def parse_pytest_output(
    output: str,
    format: str | PytestOutputFormat = PytestOutputFormat.TEXT,
) -> list[PytestIssue]:
    """Parse pytest output based on the specified format.

    Args:
        output: Raw output from pytest.
        format: Output format - accepts "json", "text", "junit" strings
            or PytestOutputFormat enum values.

    Returns:
        list[PytestIssue]: Parsed test failures and errors.
    """
    format_enum = normalize_pytest_output_format(format)

    if format_enum == PytestOutputFormat.JSON:
        return parse_pytest_json_output(output)
    elif format_enum == PytestOutputFormat.JUNIT:
        return parse_pytest_junit_xml(output)
    else:
        return parse_pytest_text_output(output)


__all__ = [
    "PytestIssue",
    "PytestSummary",
    "_parse_json_test_item",
    "extract_pytest_summary",
    "parse_pytest_json_output",
    "parse_pytest_junit_xml",
    "parse_pytest_output",
    "parse_pytest_text_output",
]
