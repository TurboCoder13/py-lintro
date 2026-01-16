"""Unit tests for gitleaks plugin error handling and edge cases."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output
from lintro.tools.definitions.gitleaks import GitleaksPlugin

# Tests for timeout handling


def test_check_with_timeout(
    gitleaks_plugin: GitleaksPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""' + chr(92) + 'n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            gitleaks_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["gitleaks"], timeout=60),
        ):
            result = gitleaks_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")


# Tests for execution failures


def test_check_with_execution_failure(
    gitleaks_plugin: GitleaksPlugin,
    tmp_path: Path,
) -> None:
    """Check handles execution failure correctly.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module."""' + chr(92) + 'n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            gitleaks_plugin,
            "_run_subprocess",
            side_effect=OSError("Failed to execute gitleaks"),
        ):
            result = gitleaks_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("Gitleaks failed")


# Tests for fix method


def test_fix_raises_not_implemented_error(
    gitleaks_plugin: GitleaksPlugin,
    tmp_path: Path,
) -> None:
    """Fix method raises NotImplementedError.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('API_KEY = "secret123"' + chr(92) + 'n')

    with pytest.raises(NotImplementedError, match="cannot automatically fix"):
        gitleaks_plugin.fix([str(test_file)], {})


# Tests for output parsing


def test_parse_gitleaks_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_gitleaks_output("")

    assert_that(issues).is_empty()


def test_parse_gitleaks_output_empty_array() -> None:
    """Parse empty JSON array returns empty list."""
    issues = parse_gitleaks_output("[]")

    assert_that(issues).is_empty()


def test_parse_gitleaks_output_single_issue() -> None:
    """Parse single issue from gitleaks output."""
    output = """[
        {
            "File": "test.py",
            "StartLine": 10,
            "StartColumn": 5,
            "EndLine": 10,
            "EndColumn": 25,
            "RuleID": "generic-api-key",
            "Description": "Generic API Key",
            "Secret": "REDACTED",
            "Fingerprint": "test.py:generic-api-key:10"
        }
    ]"""
    issues = parse_gitleaks_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].rule_id).is_equal_to("generic-api-key")
    assert_that(issues[0].description).is_equal_to("Generic API Key")


def test_parse_gitleaks_output_multiple_issues() -> None:
    """Parse multiple issues from gitleaks output."""
    output = """[
        {
            "File": "config.py",
            "StartLine": 5,
            "RuleID": "aws-access-key-id",
            "Description": "AWS Access Key ID"
        },
        {
            "File": "secrets.py",
            "StartLine": 12,
            "RuleID": "github-token",
            "Description": "GitHub Token"
        }
    ]"""
    issues = parse_gitleaks_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].rule_id).is_equal_to("aws-access-key-id")
    assert_that(issues[1].rule_id).is_equal_to("github-token")
