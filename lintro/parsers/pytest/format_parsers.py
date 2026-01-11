"""Format-specific parsers for pytest output.

This module provides functions to parse pytest output in various formats:
- JSON output from pytest --json-report
- Plain text output from pytest
- JUnit XML output from pytest --junitxml
"""

from __future__ import annotations

import json
import re

from defusedxml import ElementTree

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.pytest.pytest_issue import PytestIssue


def parse_pytest_json_output(output: str) -> list[PytestIssue]:
    """Parse pytest JSON output into PytestIssue objects.

    Args:
        output: Raw output from pytest with --json-report.

    Returns:
        list[PytestIssue]: Parsed test failures, errors, and skips.
    """
    issues: list[PytestIssue] = []

    if not output or output.strip() in ("{}", "[]"):
        return issues

    try:
        data = json.loads(output)

        # Handle different JSON report formats
        if "tests" in data:
            # pytest-json-report format
            for test in data["tests"]:
                if test.get("outcome") in ("failed", "error", "skipped"):
                    issues.append(_parse_json_test_item(test))
        elif isinstance(data, list):
            # Alternative JSON format
            for item in data:
                if isinstance(item, dict) and item.get("outcome") in (
                    "failed",
                    "error",
                    "skipped",
                ):
                    issues.append(_parse_json_test_item(item))

    except (json.JSONDecodeError, TypeError, KeyError) as e:
        from loguru import logger

        logger.debug(f"Failed to parse pytest JSON output: {e}")

    return issues


def _parse_json_test_item(test_item: dict[str, object]) -> PytestIssue:
    """Parse a single test item from JSON output.

    Args:
        test_item: Dictionary containing test information.

    Returns:
        PytestIssue: Parsed test issue.
    """
    file_raw = test_item.get("file")
    file_path = file_raw if isinstance(file_raw, str) else ""

    line_raw = test_item.get("lineno")
    line = int(line_raw) if isinstance(line_raw, int) else 0

    name_raw = test_item.get("name")
    test_name = name_raw if isinstance(name_raw, str) else ""

    call_obj = test_item.get("call")
    call_longrepr: str | None = None
    if isinstance(call_obj, dict):
        call_longrepr_val = call_obj.get("longrepr")
        if isinstance(call_longrepr_val, str):
            call_longrepr = call_longrepr_val

    longrepr_raw = test_item.get("longrepr")
    message = call_longrepr or (longrepr_raw if isinstance(longrepr_raw, str) else "")

    status_raw = test_item.get("outcome")
    status = status_raw if isinstance(status_raw, str) else "UNKNOWN"

    duration_raw = test_item.get("duration")
    if isinstance(duration_raw, (int, float)):
        duration: float | None = float(duration_raw)
    else:
        duration = 0.0

    node_id_raw = test_item.get("nodeid")
    node_id: str | None = node_id_raw if isinstance(node_id_raw, str) else ""

    return PytestIssue(
        file=file_path,
        line=line,
        test_name=test_name,
        message=message,
        test_status=status.upper(),
        duration=duration,
        node_id=node_id,
    )


def parse_pytest_text_output(output: str) -> list[PytestIssue]:
    """Parse pytest plain text output into PytestIssue objects.

    Args:
        output: Raw output from pytest.

    Returns:
        list[PytestIssue]: Parsed test failures, errors, and skips.
    """
    issues: list[PytestIssue] = []

    if not output:
        return issues

    lines = output.splitlines()
    current_file = ""
    current_line = 0

    # Patterns for different pytest output formats
    file_pattern = re.compile(r"^(.+\.py)::(.+)$")
    failure_pattern = re.compile(r"^FAILED\s+(.+\.py)::(.+)\s+-\s+(.+)$")
    error_pattern = re.compile(r"^ERROR\s+(.+\.py)::(.+)\s+-\s+(.+)$")
    skipped_pattern = re.compile(r"^(.+\.py)::([^\s]+)\s+SKIPPED\s+\((.+)\)\s+\[")
    line_pattern = re.compile(r"^(.+\.py):(\d+):\s+(.+)$")

    # Alternative patterns for different pytest output formats
    # Use non-greedy matching for test name to stop at first space
    failure_pattern_alt = re.compile(r"^FAILED\s+(.+\.py)::([^\s]+)\s+(.+)$")
    error_pattern_alt = re.compile(r"^ERROR\s+(.+\.py)::([^\s]+)\s+(.+)$")
    # Alternative skipped pattern without trailing bracket (for compact output)
    skipped_pattern_alt = re.compile(r"^(.+\.py)::([^\s]+)\s+SKIPPED\s+\((.+)\)$")

    for line in lines:
        # Strip ANSI color codes for stable parsing
        line = strip_ansi_codes(line).strip()

        # Match FAILED format
        failure_match = failure_pattern.match(line)
        if failure_match:
            file_path = failure_match.group(1)
            test_name = failure_match.group(2)
            message = failure_match.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="FAILED",
                ),
            )
            continue

        # Match FAILED format (alternative)
        failure_match_alt = failure_pattern_alt.match(line)
        if failure_match_alt:
            file_path = failure_match_alt.group(1)
            test_name = failure_match_alt.group(2)
            message = failure_match_alt.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="FAILED",
                ),
            )
            continue

        # Match ERROR format
        error_match = error_pattern.match(line)
        if error_match:
            file_path = error_match.group(1)
            test_name = error_match.group(2)
            message = error_match.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="ERROR",
                ),
            )
            continue

        # Match ERROR format (alternative)
        error_match_alt = error_pattern_alt.match(line)
        if error_match_alt:
            file_path = error_match_alt.group(1)
            test_name = error_match_alt.group(2)
            message = error_match_alt.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="ERROR",
                ),
            )
            continue

        # Match SKIPPED format
        skipped_match = skipped_pattern.match(line)
        if skipped_match:
            file_path = skipped_match.group(1)
            test_name = skipped_match.group(2)
            message = skipped_match.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="SKIPPED",
                ),
            )
            continue

        # Match SKIPPED format (alternative)
        skipped_match_alt = skipped_pattern_alt.match(line)
        if skipped_match_alt:
            file_path = skipped_match_alt.group(1)
            test_name = skipped_match_alt.group(2)
            message = skipped_match_alt.group(3)
            issues.append(
                PytestIssue(
                    file=file_path,
                    line=0,
                    test_name=test_name,
                    message=message,
                    test_status="SKIPPED",
                ),
            )
            continue

        # Match file::test format
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            continue

        # Match line number format
        line_match = line_pattern.match(line)
        if line_match:
            current_file = line_match.group(1)
            current_line = int(line_match.group(2))
            message = line_match.group(3)
            if "FAILED" in message or "ERROR" in message or "SKIPPED" in message:
                # Extract just the error message without the status prefix
                if message.startswith("FAILED - "):
                    message = message[9:]  # Remove "FAILED - "
                    status = "FAILED"
                elif message.startswith("ERROR - "):
                    message = message[8:]  # Remove "ERROR - "
                    status = "ERROR"
                elif message.startswith("SKIPPED - "):
                    message = message[10:]  # Remove "SKIPPED - "
                    status = "SKIPPED"
                else:
                    status = "UNKNOWN"

                issues.append(
                    PytestIssue(
                        file=current_file,
                        line=current_line,
                        test_name="",
                        message=message,
                        test_status=status,
                    ),
                )

    return issues


def parse_pytest_junit_xml(output: str) -> list[PytestIssue]:
    """Parse pytest JUnit XML output into PytestIssue objects.

    Args:
        output: Raw output from pytest with --junitxml.

    Returns:
        list[PytestIssue]: Parsed test failures, errors, and skips.
    """
    issues: list[PytestIssue] = []

    if not output:
        return issues

    try:
        root = ElementTree.fromstring(output)

        # Handle different JUnit XML structures
        for testcase in root.findall(".//testcase"):
            file_path = testcase.get("file", "")
            # Safely parse line number, defaulting to 0 if not numeric
            try:
                line = int(testcase.get("line", 0))
            except (ValueError, TypeError):
                line = 0
            test_name = testcase.get("name", "")
            # Safely parse duration, defaulting to 0.0 if not numeric
            try:
                duration = float(testcase.get("time", 0.0))
            except (ValueError, TypeError):
                duration = 0.0
            class_name = testcase.get("classname", "")
            # If file attribute is missing, try to derive it from classname
            if not file_path and class_name:
                # Convert class name like
                # "tests.scripts.test_script_environment.TestEnvironmentHandling"
                # to file path like "tests/scripts/test_script_environment.py"
                class_parts = class_name.split(".")
                if len(class_parts) >= 2 and class_parts[0] == "tests":
                    file_path = "/".join(class_parts[:-1]) + ".py"
            node_id = f"{class_name}::{test_name}" if class_name else test_name

            # Check for failure
            failure = testcase.find("failure")
            if failure is not None:
                message = failure.text or failure.get("message") or ""
                issues.append(
                    PytestIssue(
                        file=file_path,
                        line=line,
                        test_name=test_name,
                        message=message,
                        test_status="FAILED",
                        duration=duration,
                        node_id=node_id,
                    ),
                )

            # Check for error
            error = testcase.find("error")
            if error is not None:
                message = error.text or error.get("message") or ""
                issues.append(
                    PytestIssue(
                        file=file_path,
                        line=line,
                        test_name=test_name,
                        message=message,
                        test_status="ERROR",
                        duration=duration,
                        node_id=node_id,
                    ),
                )

            # Check for skip
            skip = testcase.find("skipped")
            if skip is not None:
                message = skip.text or skip.get("message") or ""
                # Clean up skip message by removing file path prefix if present
                # Format is typically: "/path/to/file.py:line: actual message"
                if message and ":" in message:
                    # Find the first colon after a file path pattern
                    parts = message.split(":")
                    if (
                        len(parts) >= 3
                        and parts[0].startswith("/")
                        and parts[0].endswith(".py")
                    ):
                        # Remove file path and line number, keep only the actual reason
                        message = ":".join(parts[2:]).lstrip()

                issues.append(
                    PytestIssue(
                        file=file_path,
                        line=line,
                        test_name=test_name,
                        message=message,
                        test_status="SKIPPED",
                        duration=duration,
                        node_id=node_id,
                    ),
                )

    except ElementTree.ParseError as e:
        from loguru import logger

        logger.debug(f"Failed to parse pytest JUnit XML output: {e}")

    return issues
