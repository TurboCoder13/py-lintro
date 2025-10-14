"""Parser for pytest output.

This module provides functions to parse pytest output in various formats:
- JSON output from pytest --json-report
- Plain text output from pytest
- JUnit XML output from pytest --junitxml
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from lintro.parsers.pytest.pytest_issue import PytestIssue


def parse_pytest_json_output(output: str) -> list[PytestIssue]:
    """Parse pytest JSON output into PytestIssue objects.

    Args:
        output: Raw output from pytest with --json-report.

    Returns:
        list[PytestIssue]: Parsed test failures and errors.
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
                if test.get("outcome") in ("failed", "error"):
                    issues.append(_parse_json_test_item(test))
        elif isinstance(data, list):
            # Alternative JSON format
            for item in data:
                if isinstance(item, dict) and item.get("outcome") in ("failed", "error"):
                    issues.append(_parse_json_test_item(item))
                    
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    return issues


def _parse_json_test_item(test_item: dict) -> PytestIssue:
    """Parse a single test item from JSON output.

    Args:
        test_item: Dictionary containing test information.

    Returns:
        PytestIssue: Parsed test issue.
    """
    file_path = test_item.get("file", "")
    line = test_item.get("lineno", 0)
    test_name = test_item.get("name", "")
    message = test_item.get("call", {}).get("longrepr", "") or test_item.get("longrepr", "")
    status = test_item.get("outcome", "UNKNOWN")
    duration = test_item.get("duration", 0.0)
    node_id = test_item.get("nodeid", "")

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
        list[PytestIssue]: Parsed test failures and errors.
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
    line_pattern = re.compile(r"^(.+\.py):(\d+):\s+(.+)$")
    
    # Alternative patterns for different pytest output formats
    failure_pattern_alt = re.compile(r"^FAILED\s+(.+\.py)::(.+)\s+(.+)$")
    error_pattern_alt = re.compile(r"^ERROR\s+(.+\.py)::(.+)\s+(.+)$")
    
    # Strip ANSI color codes for stable parsing
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")

    for line in lines:
        # Strip ANSI color codes for stable parsing
        line = ansi_re.sub("", line).strip()
        
        # Match FAILED format
        failure_match = failure_pattern.match(line)
        if failure_match:
            file_path = failure_match.group(1)
            test_name = failure_match.group(2)
            message = failure_match.group(3)
            issues.append(PytestIssue(
                file=file_path,
                line=0,
                test_name=test_name,
                message=message,
                test_status="FAILED",
            ))
            continue

        # Match FAILED format (alternative)
        failure_match_alt = failure_pattern_alt.match(line)
        if failure_match_alt:
            file_path = failure_match_alt.group(1)
            test_name = failure_match_alt.group(2)
            message = failure_match_alt.group(3)
            issues.append(PytestIssue(
                file=file_path,
                line=0,
                test_name=test_name,
                message=message,
                test_status="FAILED",
            ))
            continue

        # Match ERROR format
        error_match = error_pattern.match(line)
        if error_match:
            file_path = error_match.group(1)
            test_name = error_match.group(2)
            message = error_match.group(3)
            issues.append(PytestIssue(
                file=file_path,
                line=0,
                test_name=test_name,
                message=message,
                test_status="ERROR",
            ))
            continue

        # Match ERROR format (alternative)
        error_match_alt = error_pattern_alt.match(line)
        if error_match_alt:
            file_path = error_match_alt.group(1)
            test_name = error_match_alt.group(2)
            message = error_match_alt.group(3)
            issues.append(PytestIssue(
                file=file_path,
                line=0,
                test_name=test_name,
                message=message,
                test_status="ERROR",
            ))
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
            if "FAILED" in message or "ERROR" in message:
                # Extract just the error message without the status prefix
                if message.startswith("FAILED - "):
                    message = message[9:]  # Remove "FAILED - "
                elif message.startswith("ERROR - "):
                    message = message[8:]   # Remove "ERROR - "
                
                issues.append(PytestIssue(
                    file=current_file,
                    line=current_line,
                    test_name="",
                    message=message,
                    test_status="FAILED" if "FAILED" in line_match.group(3) else "ERROR",
                ))

    return issues


def parse_pytest_junit_xml(output: str) -> list[PytestIssue]:
    """Parse pytest JUnit XML output into PytestIssue objects.

    Args:
        output: Raw output from pytest with --junitxml.

    Returns:
        list[PytestIssue]: Parsed test failures and errors.
    """
    issues: list[PytestIssue] = []

    if not output:
        return issues

    try:
        root = ET.fromstring(output)
        
        # Handle different JUnit XML structures
        for testcase in root.findall(".//testcase"):
            file_path = testcase.get("file", "")
            line = int(testcase.get("line", 0))
            test_name = testcase.get("name", "")
            duration = float(testcase.get("time", 0.0))
            class_name = testcase.get("classname", "")
            node_id = f"{class_name}::{test_name}" if class_name else test_name

            # Check for failure
            failure = testcase.find("failure")
            if failure is not None:
                message = failure.text or failure.get("message", "")
                issues.append(PytestIssue(
                    file=file_path,
                    line=line,
                    test_name=test_name,
                    message=message,
                    test_status="FAILED",
                    duration=duration,
                    node_id=node_id,
                ))

            # Check for error
            error = testcase.find("error")
            if error is not None:
                message = error.text or error.get("message", "")
                issues.append(PytestIssue(
                    file=file_path,
                    line=line,
                    test_name=test_name,
                    message=message,
                    test_status="ERROR",
                    duration=duration,
                    node_id=node_id,
                ))

    except ET.ParseError:
        pass

    return issues


def parse_pytest_output(output: str, format: str = "text") -> list[PytestIssue]:
    """Parse pytest output based on the specified format.

    Args:
        output: Raw output from pytest.
        format: Output format ("json", "text", "junit").

    Returns:
        list[PytestIssue]: Parsed test failures and errors.
    """
    if format == "json":
        return parse_pytest_json_output(output)
    elif format == "junit":
        return parse_pytest_junit_xml(output)
    else:
        return parse_pytest_text_output(output)
