"""Unit tests for Semgrep plugin."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.semgrep.semgrep_parser import parse_semgrep_output
from lintro.tools.definitions.semgrep import (
    SEMGREP_DEFAULT_CONFIG,
    SEMGREP_DEFAULT_TIMEOUT,
    SemgrepPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def semgrep_plugin() -> SemgrepPlugin:
    """Provide a SemgrepPlugin instance for testing.

    Returns:
        A SemgrepPlugin instance with mocked version verification.
    """
    with patch.object(SemgrepPlugin, "_verify_tool_version", return_value=None):
        return SemgrepPlugin()


# Tests for SemgrepPlugin default options


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", SEMGREP_DEFAULT_TIMEOUT),
        ("config", SEMGREP_DEFAULT_CONFIG),
        ("exclude", None),
        ("include", None),
        ("severity", None),
        ("timeout_threshold", None),
        ("jobs", None),
        ("verbose", False),
        ("quiet", False),
    ],
    ids=[
        "timeout_equals_default",
        "config_equals_auto",
        "exclude_is_none",
        "include_is_none",
        "severity_is_none",
        "timeout_threshold_is_none",
        "jobs_is_none",
        "verbose_is_false",
        "quiet_is_false",
    ],
)
def test_default_options_values(
    semgrep_plugin: SemgrepPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        semgrep_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for SemgrepPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("config", "auto"),
        ("config", "p/python"),
        ("config", "p/javascript"),
        ("config", "/path/to/rules.yaml"),
        ("exclude", ["test_*.py", "vendor/*"]),
        ("include", ["src/*.py", "lib/*.py"]),
        ("severity", "INFO"),
        ("severity", "WARNING"),
        ("severity", "ERROR"),
        ("jobs", 4),
        ("jobs", 1),
        ("timeout_threshold", 30),
        ("timeout_threshold", 0),
        ("verbose", True),
        ("quiet", True),
    ],
    ids=[
        "config_auto",
        "config_python_ruleset",
        "config_javascript_ruleset",
        "config_custom_path",
        "exclude_patterns",
        "include_patterns",
        "severity_info",
        "severity_warning",
        "severity_error",
        "jobs_4",
        "jobs_1",
        "timeout_threshold_30",
        "timeout_threshold_0",
        "verbose_true",
        "quiet_true",
    ],
)
def test_set_options_valid(
    semgrep_plugin: SemgrepPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    semgrep_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]

    # Severity is normalized to uppercase
    if option_name == "severity" and isinstance(option_value, str):
        expected = option_value.upper()
    else:
        expected = option_value

    assert_that(semgrep_plugin.options.get(option_name)).is_equal_to(expected)


def test_set_options_severity_lowercase(semgrep_plugin: SemgrepPlugin) -> None:
    """Set severity option with lowercase value normalizes to uppercase.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(severity="info")
    assert_that(semgrep_plugin.options.get("severity")).is_equal_to("INFO")


# Tests for SemgrepPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("severity", "CRITICAL", "severity must be one of"),
        ("severity", "invalid", "severity must be one of"),
        ("jobs", 0, "jobs must be a positive integer"),
        ("jobs", -1, "jobs must be a positive integer"),
        ("jobs", "four", "jobs must be a positive integer"),
        ("timeout_threshold", -1, "timeout_threshold must be a non-negative integer"),
        ("timeout_threshold", "slow", "timeout_threshold must be a non-negative integer"),
        ("exclude", "*.py", "exclude must be a list"),
        ("include", "*.py", "include must be a list"),
        ("config", 123, "config must be a string"),
    ],
    ids=[
        "invalid_severity_critical",
        "invalid_severity_unknown",
        "invalid_jobs_zero",
        "invalid_jobs_negative",
        "invalid_jobs_type",
        "invalid_timeout_threshold_negative",
        "invalid_timeout_threshold_type",
        "invalid_exclude_type",
        "invalid_include_type",
        "invalid_config_type",
    ],
)
def test_set_options_invalid_type(
    semgrep_plugin: SemgrepPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        semgrep_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for SemgrepPlugin._build_check_command method


def test_build_check_command_basic(semgrep_plugin: SemgrepPlugin) -> None:
    """Build basic command with default options.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("semgrep")
    assert_that(cmd).contains("scan")
    assert_that(cmd).contains("--json")
    assert_that(cmd).contains("--config")
    # Default config is "auto"
    config_idx = cmd.index("--config")
    assert_that(cmd[config_idx + 1]).is_equal_to("auto")
    assert_that(cmd).contains("src/")


def test_build_check_command_with_config(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with custom config option.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(config="p/python")
    cmd = semgrep_plugin._build_check_command(files=["app.py"])

    assert_that(cmd).contains("--config")
    config_idx = cmd.index("--config")
    assert_that(cmd[config_idx + 1]).is_equal_to("p/python")


def test_build_check_command_with_exclude(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with exclude patterns.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(exclude=["tests/*", "vendor/*"])
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    # Each exclude pattern should have its own --exclude flag
    exclude_indices = [i for i, x in enumerate(cmd) if x == "--exclude"]
    assert_that(exclude_indices).is_length(2)
    assert_that(cmd[exclude_indices[0] + 1]).is_equal_to("tests/*")
    assert_that(cmd[exclude_indices[1] + 1]).is_equal_to("vendor/*")


def test_build_check_command_with_include(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with include patterns.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(include=["*.py", "*.js"])
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    # Each include pattern should have its own --include flag
    include_indices = [i for i, x in enumerate(cmd) if x == "--include"]
    assert_that(include_indices).is_length(2)
    assert_that(cmd[include_indices[0] + 1]).is_equal_to("*.py")
    assert_that(cmd[include_indices[1] + 1]).is_equal_to("*.js")


def test_build_check_command_with_severity(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with severity filter.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(severity="ERROR")
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("--severity")
    severity_idx = cmd.index("--severity")
    assert_that(cmd[severity_idx + 1]).is_equal_to("ERROR")


def test_build_check_command_with_jobs(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with jobs option.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(jobs=4)
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("--jobs")
    jobs_idx = cmd.index("--jobs")
    assert_that(cmd[jobs_idx + 1]).is_equal_to("4")


def test_build_check_command_with_timeout_threshold(
    semgrep_plugin: SemgrepPlugin,
) -> None:
    """Build command with timeout_threshold option.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(timeout_threshold=30)
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("--timeout")
    timeout_idx = cmd.index("--timeout")
    assert_that(cmd[timeout_idx + 1]).is_equal_to("30")


def test_build_check_command_with_verbose(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with verbose flag.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(verbose=True)
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("--verbose")


def test_build_check_command_with_quiet(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with quiet flag.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(quiet=True)
    cmd = semgrep_plugin._build_check_command(files=["src/"])

    assert_that(cmd).contains("--quiet")


def test_build_check_command_with_all_options(semgrep_plugin: SemgrepPlugin) -> None:
    """Build command with all options set.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    semgrep_plugin.set_options(
        config="p/security-audit",
        exclude=["tests/*"],
        include=["*.py"],
        severity="WARNING",
        timeout_threshold=60,
        jobs=8,
        verbose=True,
    )
    cmd = semgrep_plugin._build_check_command(files=["src/", "lib/"])

    assert_that(cmd).contains("--config")
    assert_that(cmd).contains("--exclude")
    assert_that(cmd).contains("--include")
    assert_that(cmd).contains("--severity")
    assert_that(cmd).contains("--timeout")
    assert_that(cmd).contains("--jobs")
    assert_that(cmd).contains("--verbose")
    assert_that(cmd).contains("src/")
    assert_that(cmd).contains("lib/")


# Tests for SemgrepPlugin.check method


def test_check_with_mocked_subprocess_success(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no issues found.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "clean_code.py"
    test_file.write_text('"""Clean module with no security issues."""\n')

    # Semgrep JSON output with no results
    semgrep_output = json.dumps({"results": [], "errors": []})

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            return_value=(True, semgrep_output),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_findings(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when Semgrep finds security problems.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "vulnerable.py"
    test_file.write_text('import os\nos.system(user_input)\n')

    # Semgrep JSON output with findings
    semgrep_output = json.dumps({
        "results": [
            {
                "check_id": "python.lang.security.audit.dangerous-system-call",
                "path": str(test_file),
                "start": {"line": 2, "col": 1},
                "end": {"line": 2, "col": 25},
                "extra": {
                    "message": "Detected dangerous system call with user input",
                    "severity": "ERROR",
                    "metadata": {
                        "category": "security",
                        "cwe": ["CWE-78"],
                    },
                },
            },
        ],
        "errors": [],
    })

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            return_value=(False, semgrep_output),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()  # No errors in response
    assert_that(result.issues_count).is_equal_to(1)
    assert_that(result.issues).is_length(1)
    assert_that(result.issues[0].check_id).is_equal_to(
        "python.lang.security.audit.dangerous-system-call",
    )


def test_check_with_timeout(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "large_file.py"
    test_file.write_text('"""Large file that takes too long."""\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["semgrep"], timeout=120),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")


def test_check_with_json_parse_error(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check handles JSON parse errors gracefully.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""\n')

    # Invalid JSON output
    invalid_output = "Error: Something went wrong\n{invalid json"

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            return_value=(False, invalid_output),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_multiple_findings(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check handles multiple findings correctly.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "multiple_issues.py"
    test_file.write_text('import os\nos.system(x)\neval(y)\n')

    # Semgrep JSON output with multiple findings
    semgrep_output = json.dumps({
        "results": [
            {
                "check_id": "python.lang.security.audit.dangerous-system-call",
                "path": str(test_file),
                "start": {"line": 2, "col": 1},
                "end": {"line": 2, "col": 15},
                "extra": {
                    "message": "Dangerous system call",
                    "severity": "ERROR",
                    "metadata": {"category": "security"},
                },
            },
            {
                "check_id": "python.lang.security.audit.eval-usage",
                "path": str(test_file),
                "start": {"line": 3, "col": 1},
                "end": {"line": 3, "col": 8},
                "extra": {
                    "message": "Use of eval() detected",
                    "severity": "WARNING",
                    "metadata": {"category": "security"},
                },
            },
        ],
        "errors": [],
    })

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            return_value=(False, semgrep_output),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.issues_count).is_equal_to(2)
    assert_that(result.issues).is_length(2)


def test_check_with_semgrep_errors(
    semgrep_plugin: SemgrepPlugin,
    tmp_path: Path,
) -> None:
    """Check handles Semgrep errors in response.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""\n')

    # Semgrep JSON output with errors
    semgrep_output = json.dumps({
        "results": [],
        "errors": [
            {"message": "Failed to fetch rules from registry"},
        ],
    })

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            semgrep_plugin,
            "_run_subprocess",
            return_value=(False, semgrep_output),
        ):
            result = semgrep_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()


# Tests for SemgrepPlugin.fix method


def test_fix_raises_not_implemented(semgrep_plugin: SemgrepPlugin) -> None:
    """Fix method raises NotImplementedError.

    Args:
        semgrep_plugin: The SemgrepPlugin instance to test.
    """
    with pytest.raises(NotImplementedError, match="cannot automatically fix"):
        semgrep_plugin.fix(["src/"], {})


# Tests for output parsing


def test_parse_semgrep_output_single_issue() -> None:
    """Parse single issue from Semgrep output."""
    output = json.dumps({
        "results": [
            {
                "check_id": "python.lang.security.audit.eval-usage",
                "path": "test.py",
                "start": {"line": 10, "col": 1},
                "end": {"line": 10, "col": 15},
                "extra": {
                    "message": "Detected use of eval()",
                    "severity": "WARNING",
                    "metadata": {"category": "security"},
                },
            },
        ],
    })
    issues = parse_semgrep_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].check_id).is_equal_to("python.lang.security.audit.eval-usage")
    assert_that(issues[0].message).contains("eval()")


def test_parse_semgrep_output_multiple_issues() -> None:
    """Parse multiple issues from Semgrep output."""
    output = json.dumps({
        "results": [
            {
                "check_id": "rule1",
                "path": "file1.py",
                "start": {"line": 5, "col": 1},
                "end": {"line": 5, "col": 10},
                "extra": {
                    "message": "Issue 1",
                    "severity": "ERROR",
                    "metadata": {},
                },
            },
            {
                "check_id": "rule2",
                "path": "file2.py",
                "start": {"line": 15, "col": 1},
                "end": {"line": 15, "col": 20},
                "extra": {
                    "message": "Issue 2",
                    "severity": "WARNING",
                    "metadata": {},
                },
            },
        ],
    })
    issues = parse_semgrep_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].check_id).is_equal_to("rule1")
    assert_that(issues[1].check_id).is_equal_to("rule2")


def test_parse_semgrep_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_semgrep_output("")

    assert_that(issues).is_empty()


def test_parse_semgrep_output_empty_results() -> None:
    """Parse output with no results returns empty list."""
    output = json.dumps({"results": []})
    issues = parse_semgrep_output(output)

    assert_that(issues).is_empty()


def test_parse_semgrep_output_with_cwe() -> None:
    """Parse output with CWE information."""
    output = json.dumps({
        "results": [
            {
                "check_id": "security-rule",
                "path": "app.py",
                "start": {"line": 20, "col": 1},
                "end": {"line": 20, "col": 30},
                "extra": {
                    "message": "SQL injection vulnerability",
                    "severity": "ERROR",
                    "metadata": {
                        "category": "security",
                        "cwe": ["CWE-89"],
                    },
                },
            },
        ],
    })
    issues = parse_semgrep_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].cwe).contains("CWE-89")


def test_parse_semgrep_output_none_input() -> None:
    """Parse None input returns empty list."""
    issues = parse_semgrep_output(None)

    assert_that(issues).is_empty()
