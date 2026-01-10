"""Summary extraction from pytest output.

This module provides functions to extract summary statistics from pytest output.
"""

from __future__ import annotations

import re

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.pytest.models import PytestSummary


def extract_pytest_summary(output: str) -> PytestSummary:
    """Extract test summary statistics from pytest output.

    Parses the summary line from pytest output to extract:
    - Number of passed tests
    - Number of failed tests
    - Number of skipped tests
    - Number of error tests
    - Execution duration

    Args:
        output: Raw output from pytest.

    Returns:
        PytestSummary: Extracted summary statistics.
    """
    summary = PytestSummary()

    if not output:
        return summary

    # Strip ANSI color codes
    clean_output = strip_ansi_codes(output)

    # Extract duration first (it's always at the end)
    duration_match = re.search(r"in\s+([\d.]+)s", clean_output)
    if duration_match:
        summary.duration = float(duration_match.group(1))

    # Extract counts independently since order can vary
    # Patterns handle various formats like:
    # - "511 passed in 18.53s"
    # - "509 passed, 2 failed in 18.53s"
    # - "7 failed, 505 passed, 1 warning in 18.53s"
    # - "510 passed, 1 skipped in 18.53s"

    passed_match = re.search(r"(\d+)\s+passed", clean_output)
    if passed_match:
        summary.passed = int(passed_match.group(1))

    failed_match = re.search(r"(\d+)\s+failed", clean_output)
    if failed_match:
        summary.failed = int(failed_match.group(1))

    skipped_match = re.search(r"(\d+)\s+skipped", clean_output)
    if skipped_match:
        summary.skipped = int(skipped_match.group(1))

    error_match = re.search(r"(\d+)\s+errors?", clean_output)
    if error_match:
        summary.error = int(error_match.group(1))

    xfailed_match = re.search(r"(\d+)\s+xfailed", clean_output)
    if xfailed_match:
        summary.xfailed = int(xfailed_match.group(1))

    xpassed_match = re.search(r"(\d+)\s+xpassed", clean_output)
    if xpassed_match:
        summary.xpassed = int(xpassed_match.group(1))

    # Calculate total as sum of all test outcomes
    summary.total = (
        summary.passed
        + summary.failed
        + summary.skipped
        + summary.error
        + summary.xfailed
        + summary.xpassed
    )

    return summary
