"""Output processing functions for pytest tool.

This module contains output parsing, summary extraction, performance warnings,
and flaky test detection logic extracted from PytestTool to improve
maintainability and reduce file size.
"""

import json
from pathlib import Path

from loguru import logger

from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.parsers.pytest.pytest_parser import (
    extract_pytest_summary,
    parse_pytest_output,
)
from lintro.tools.implementations.pytest.collection import (
    compute_updated_flaky_test_history,
    save_flaky_test_history,
)
from lintro.tools.implementations.pytest.pytest_utils import (
    detect_flaky_tests,
    extract_all_test_results_from_junit,
    is_ci_environment,
)

# Constants for pytest configuration
PYTEST_SLOW_TEST_THRESHOLD: float = 1.0  # Warn if any test takes > 1 second
PYTEST_TOTAL_TIME_WARNING: float = 60.0  # Warn if total execution time > 60 seconds
PYTEST_FLAKY_MIN_RUNS: int = 3  # Minimum runs before detecting flaky tests
PYTEST_FLAKY_FAILURE_RATE: float = 0.3  # Consider flaky if fails >= 30% but < 100%


def parse_pytest_output_with_fallback(
    output: str,
    return_code: int,
    options: dict,
    subprocess_start_time: float | None = None,
) -> list[PytestIssue]:
    """Parse pytest output into issues with format detection and fallback.

    Prioritizes JSON format when available, then JUnit XML, then falls back to text.
    Validates parsed output structure to ensure reliability.
    Always tries to parse JUnit XML file if available to capture skipped tests.

    Args:
        output: Raw output from pytest.
        return_code: Return code from pytest.
        options: Options dictionary.
        subprocess_start_time: Optional Unix timestamp when subprocess started.
            If provided, only JUnit XML files modified after this time will be read.

    Returns:
        list[PytestIssue]: Parsed test failures, errors, and skips.
    """
    issues = []

    # Try to parse JUnit XML file if it exists and was explicitly requested
    # This captures all test results including skips when using JUnit XML format
    # But only if the output we're parsing is not already JUnit XML
    # AND we're not in JSON mode (prioritize JSON over JUnit XML)
    # Check this BEFORE early return to ensure JUnit XML parsing happens even
    # when output is empty (e.g., quiet mode or redirected output)
    junitxml_path = None
    if (
        options.get("junitxml")
        and (not output or not output.strip().startswith("<?xml"))
        and not options.get("json_report", False)
    ):
        junitxml_path = options.get("junitxml")

    # Early return only if output is empty AND no JUnit XML file to parse
    if not output and not (junitxml_path and Path(junitxml_path).exists()):
        return []

    if junitxml_path and Path(junitxml_path).exists():
        # Only read the file if it was modified after subprocess started
        # This prevents reading stale files from previous test runs
        junitxml_file = Path(junitxml_path)
        file_mtime = junitxml_file.stat().st_mtime
        should_read = True

        if subprocess_start_time is not None and file_mtime < subprocess_start_time:
            logger.debug(
                f"Skipping stale JUnit XML file {junitxml_path} "
                f"(modified before subprocess started)",
            )
            should_read = False

        if should_read:
            try:
                with open(junitxml_path, encoding="utf-8") as f:
                    junit_content = f.read()
                junit_issues = parse_pytest_output(junit_content, format="junit")
                if junit_issues:
                    issues.extend(junit_issues)
                    logger.debug(
                        f"Parsed {len(junit_issues)} issues from JUnit XML file",
                    )
            except OSError as e:
                logger.debug(f"Failed to read JUnit XML file {junitxml_path}: {e}")

    # If we already have issues from JUnit XML, return them
    # Otherwise, fall back to parsing the output
    if issues:
        return issues

    # Try to detect output format automatically
    # Priority: JSON > JUnit XML > Text
    output_format = "text"

    # Check for JSON format (pytest-json-report)
    if options.get("json_report", False):
        output_format = "json"
    elif options.get("junitxml"):
        output_format = "junit"
    else:
        # Auto-detect format from output content
        # Check for JSON report file reference or JSON content
        if "pytest-report.json" in output or (
            output.strip().startswith("{") and "test_reports" in output
        ):
            output_format = "json"
        # Check for JUnit XML structure
        elif output.strip().startswith("<?xml") and "<testsuite" in output:
            output_format = "junit"
        # Default to text parsing
        else:
            output_format = "text"

    # Parse based on detected format
    issues = parse_pytest_output(output, format=output_format)

    # Validate parsed output structure
    if not isinstance(issues, list):
        logger.warning(
            f"Parser returned unexpected type: {type(issues)}, "
            "falling back to text parsing",
        )
        issues = []
    else:
        # Validate that all items are PytestIssue instances
        validated_issues = []
        for issue in issues:
            if isinstance(issue, PytestIssue):
                validated_issues.append(issue)
            else:
                logger.warning(
                    f"Skipping invalid issue type: {type(issue)}",
                )
        issues = validated_issues

    # If no issues found but return code indicates failure, try text parsing
    if not issues and return_code != 0 and output_format != "text":
        logger.debug(
            f"No issues parsed from {output_format} format, "
            "trying text parsing fallback",
        )
        fallback_issues = parse_pytest_output(output, format="text")
        if fallback_issues:
            logger.info(
                f"Fallback text parsing found {len(fallback_issues)} issues",
            )
            issues = fallback_issues

    return issues


def process_test_summary(
    output: str,
    issues: list[PytestIssue],
    total_available_tests: int,
    docker_test_count: int,
    run_docker_tests: bool,
) -> dict:
    """Process test summary and calculate skipped tests.

    Args:
        output: Raw output from pytest.
        issues: Parsed test issues.
        total_available_tests: Total number of available tests.
        docker_test_count: Number of docker tests.
        run_docker_tests: Whether docker tests were enabled.

    Returns:
        dict: Summary data dictionary.
    """
    # Extract summary statistics
    summary = extract_pytest_summary(output)

    # Filter to only failed/error issues for display
    failed_issues = [
        issue for issue in issues if issue.test_status in ("FAILED", "ERROR")
    ]

    # Use actual failed issues count, not summary count
    # (in case parsing is inconsistent)
    actual_failures = len(failed_issues)

    # Calculate docker skipped tests
    # If docker tests are disabled and we have some,
    # they should show as skipped in the output
    docker_skipped = 0
    if not run_docker_tests and docker_test_count > 0:
        # When Docker tests are disabled, they are deselected by pytest
        # so they won't appear in summary.skipped
        docker_skipped = docker_test_count

    # Calculate actual skipped tests (tests that exist but weren't run)
    # This includes deselected tests that pytest doesn't report in summary
    # Note: summary.error is already counted in actual_failures, so don't double-count
    # Include xfailed and xpassed in collected count as they are tests that ran
    collected_tests = (
        summary.passed
        + actual_failures
        + summary.skipped
        + summary.xfailed
        + summary.xpassed
    )
    actual_skipped = max(0, total_available_tests - collected_tests)

    logger.debug(f"Total available tests: {total_available_tests}")
    logger.debug(f"Collected tests: {collected_tests}")
    logger.debug(
        f"Summary: passed={summary.passed}, "
        f"failed={actual_failures}, "
        f"skipped={summary.skipped}, "
        f"error={summary.error}",
    )
    logger.debug(f"Actual skipped: {actual_skipped}")
    logger.debug(f"Docker skipped: {docker_skipped}")

    # Use the larger of summary.skipped or actual_skipped
    # (summary.skipped is runtime skips, actual_skipped includes deselected)
    # But ensure docker_skipped is included in the total
    total_skipped = max(summary.skipped, actual_skipped)

    # Ensure docker_skipped is included in the total skipped count
    # This makes Docker tests show as skipped when --enable-docker is not used
    if docker_skipped > 0 and total_skipped < docker_skipped:
        total_skipped = docker_skipped

    summary_data = {
        "passed": summary.passed,
        # Use actual parsed failures, not regex summary
        "failed": actual_failures,
        "skipped": total_skipped,
        "error": summary.error,
        "docker_skipped": docker_skipped,
        "duration": summary.duration,
        "total": total_available_tests,
    }

    return summary_data


def detect_and_log_slow_tests(
    issues: list[PytestIssue],
    options: dict,
) -> list[tuple[str, float]]:
    """Detect slow tests and log warnings.

    Args:
        issues: List of parsed test issues.
        options: Options dictionary.

    Returns:
        list[tuple[str, float]]: List of (test_name, duration) tuples for slow tests.
    """
    slow_tests: list[tuple[str, float]] = []
    # Check all issues (including passed tests) for slow tests
    if issues:
        # Find slow tests (individual test duration > threshold)
        slow_threshold = options.get(
            "slow_test_threshold",
            PYTEST_SLOW_TEST_THRESHOLD,
        )
        for issue in issues:
            if (
                issue.duration
                and isinstance(issue.duration, (int, float))
                and issue.duration > slow_threshold
            ):
                slow_tests.append((issue.test_name, issue.duration))

    # Log slow test files
    if slow_tests:
        # Sort by duration descending
        slow_tests.sort(key=lambda x: x[1], reverse=True)
        slow_threshold = options.get(
            "slow_test_threshold",
            PYTEST_SLOW_TEST_THRESHOLD,
        )
        slow_msg = f"🐌 Found {len(slow_tests)} slow test(s) (> {slow_threshold}s):"
        logger.info(slow_msg)
        for test_name, duration in slow_tests[:10]:  # Show top 10 slowest
            logger.info(f"  - {test_name}: {duration:.2f}s")
        if len(slow_tests) > 10:
            logger.info(f"  ... and {len(slow_tests) - 10} more")

    return slow_tests


def check_total_time_warning(
    summary_duration: float,
    options: dict,
) -> None:
    """Check and warn if total execution time exceeds threshold.

    Args:
        summary_duration: Total test execution duration.
        options: Options dictionary.
    """
    total_time_warning = options.get(
        "total_time_warning",
        PYTEST_TOTAL_TIME_WARNING,
    )
    if summary_duration > total_time_warning:
        warning_msg = (
            f"⚠️  Tests took {summary_duration:.1f}s to run "
            f"(threshold: {total_time_warning}s). "
            "Consider optimizing slow tests or enabling parallel execution "
            "with --tool-options workers=auto"
        )
        logger.warning(warning_msg)


def detect_and_log_flaky_tests(
    issues: list[PytestIssue],
    options: dict,
) -> list[tuple[str, float]]:
    """Detect flaky tests and log warnings.

    Args:
        issues: List of parsed test issues.
        options: Options dictionary.

    Returns:
        list[tuple[str, float]]: List of (node_id, failure_rate) tuples for flaky tests.
    """
    enable_flaky_detection = options.get("detect_flaky", True)
    flaky_tests: list[tuple[str, float]] = []
    if enable_flaky_detection:
        # Try to get all test results from JUnit XML if available
        all_test_results: dict[str, str] | None = None
        junitxml_path = options.get("junitxml") or (
            "report.xml" if is_ci_environment() else None
        )
        if junitxml_path and Path(junitxml_path).exists():
            all_test_results = extract_all_test_results_from_junit(
                junitxml_path,
            )

        # Update flaky test history
        history = compute_updated_flaky_test_history(issues, all_test_results)
        save_flaky_test_history(history)

        # Detect flaky tests
        min_runs = options.get("flaky_min_runs", PYTEST_FLAKY_MIN_RUNS)
        failure_rate = options.get(
            "flaky_failure_rate",
            PYTEST_FLAKY_FAILURE_RATE,
        )
        flaky_tests = detect_flaky_tests(history, min_runs, failure_rate)

        # Report flaky tests
        if flaky_tests:
            flaky_msg = f"⚠️  Found {len(flaky_tests)} potentially flaky test(s):"
            logger.warning(flaky_msg)
            for node_id, rate in flaky_tests[:10]:  # Show top 10 flakiest
                logger.warning(
                    f"  - {node_id}: {rate:.0%} failure rate "
                    f"({history[node_id]['failed'] + history[node_id]['error']}"
                    f" failures in {sum(history[node_id].values())} runs)",
                )
            if len(flaky_tests) > 10:
                logger.warning(f"  ... and {len(flaky_tests) - 10} more")

    return flaky_tests


def build_output_with_failures(
    summary_data: dict,
    all_issues: list[PytestIssue],
) -> str:
    """Build output string with summary and test details.

    Args:
        summary_data: Summary data dictionary.
        all_issues: List of all test issues (failures, errors, skips).

    Returns:
        str: Formatted output string.
    """
    # Build output with summary and test details
    output_lines = [json.dumps(summary_data)]

    # Format issues as tables (failures and skipped tests)
    if all_issues:
        # Import the pytest formatter to format issues as tables
        from lintro.formatters.tools.pytest_formatter import (
            format_pytest_issues,
        )

        # Format issues as tables (includes both failures and skipped tests)
        issues_tables = format_pytest_issues(all_issues, format="grid")
        if issues_tables.strip():
            output_lines.append("")  # Blank line before tables
            output_lines.append(issues_tables)

    return "\n".join(output_lines)
