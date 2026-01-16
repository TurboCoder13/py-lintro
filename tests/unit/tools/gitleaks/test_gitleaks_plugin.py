"""Unit tests for gitleaks plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output
from lintro.tools.definitions.gitleaks import (
    GITLEAKS_DEFAULT_TIMEOUT,
    GITLEAKS_OUTPUT_FORMAT,
    GitleaksPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def gitleaks_plugin() -> GitleaksPlugin:
    """Provide a GitleaksPlugin instance for testing.

    Returns:
        A GitleaksPlugin instance with mocked version verification.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return GitleaksPlugin()


# Tests for default options


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", GITLEAKS_DEFAULT_TIMEOUT),
        ("no_git", True),
        ("config", None),
        ("baseline_path", None),
        ("redact", True),
        ("max_target_megabytes", None),
    ],
    ids=[
        "timeout_equals_default",
        "no_git_is_true",
        "config_is_none",
        "baseline_path_is_none",
        "redact_is_true",
        "max_target_megabytes_is_none",
    ],
)
def test_default_options_values(
    gitleaks_plugin: GitleaksPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        gitleaks_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for GitleaksPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("no_git", False),
        ("config", "/path/to/.gitleaks.toml"),
        ("baseline_path", "/path/to/baseline.json"),
        ("redact", False),
        ("max_target_megabytes", 100),
    ],
    ids=[
        "no_git_false",
        "config_path",
        "baseline_path",
        "redact_false",
        "max_target_megabytes_100",
    ],
)
def test_set_options_valid(
    gitleaks_plugin: GitleaksPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    gitleaks_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(gitleaks_plugin.options.get(option_name)).is_equal_to(option_value)


# Tests for GitleaksPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("no_git", "yes", "no_git must be a boolean"),
        ("no_git", 1, "no_git must be a boolean"),
        ("config", 123, "config must be a string"),
        ("config", True, "config must be a string"),
        ("baseline_path", 456, "baseline_path must be a string"),
        ("max_target_megabytes", "large", "max_target_megabytes must be an integer"),
        ("max_target_megabytes", -1, "max_target_megabytes must be positive"),
        ("max_target_megabytes", 0, "max_target_megabytes must be positive"),
        ("redact", "true", "redact must be a boolean"),
    ],
    ids=[
        "invalid_no_git_string",
        "invalid_no_git_int",
        "invalid_config_int",
        "invalid_config_bool",
        "invalid_baseline_path_int",
        "invalid_max_target_megabytes_string",
        "invalid_max_target_megabytes_negative",
        "invalid_max_target_megabytes_zero",
        "invalid_redact_string",
    ],
)
def test_set_options_invalid_type(
    gitleaks_plugin: GitleaksPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        gitleaks_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for GitleaksPlugin._build_check_command method


def test_build_check_command_basic(gitleaks_plugin: GitleaksPlugin) -> None:
    """Build basic command with default options.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).contains("gitleaks")
    assert_that(cmd).contains("detect")
    assert_that(cmd).contains("--source")
    assert_that(cmd).contains("/path/to/source")
    # Default no_git=True should add --no-git
    assert_that(cmd).contains("--no-git")
    # Default redact=True should add --redact
    assert_that(cmd).contains("--redact")
    # Output format should be JSON
    assert_that(cmd).contains("--report-format")
    assert_that(cmd).contains(GITLEAKS_OUTPUT_FORMAT)


def test_build_check_command_with_no_git_false(gitleaks_plugin: GitleaksPlugin) -> None:
    """Build command without --no-git flag when no_git=False.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(no_git=False)
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).does_not_contain("--no-git")


def test_build_check_command_with_config(gitleaks_plugin: GitleaksPlugin) -> None:
    """Build command with config file path.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(config="/path/to/.gitleaks.toml")
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).contains("--config")
    config_idx = cmd.index("--config")
    assert_that(cmd[config_idx + 1]).is_equal_to("/path/to/.gitleaks.toml")


def test_build_check_command_with_baseline_path(
    gitleaks_plugin: GitleaksPlugin,
) -> None:
    """Build command with baseline path.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(baseline_path="/path/to/baseline.json")
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).contains("--baseline-path")
    baseline_idx = cmd.index("--baseline-path")
    assert_that(cmd[baseline_idx + 1]).is_equal_to("/path/to/baseline.json")


def test_build_check_command_with_max_target_megabytes(
    gitleaks_plugin: GitleaksPlugin,
) -> None:
    """Build command with max target megabytes.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(max_target_megabytes=100)
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).contains("--max-target-megabytes")
    max_mb_idx = cmd.index("--max-target-megabytes")
    assert_that(cmd[max_mb_idx + 1]).is_equal_to("100")


def test_build_check_command_with_redact_false(
    gitleaks_plugin: GitleaksPlugin,
) -> None:
    """Build command without --redact flag when redact=False.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(redact=False)
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).does_not_contain("--redact")


def test_build_check_command_with_all_options(gitleaks_plugin: GitleaksPlugin) -> None:
    """Build command with all options set.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
    """
    gitleaks_plugin.set_options(
        no_git=False,
        config="/path/to/.gitleaks.toml",
        baseline_path="/path/to/baseline.json",
        redact=True,
        max_target_megabytes=50,
    )
    cmd = gitleaks_plugin._build_check_command(source_path="/path/to/source")

    assert_that(cmd).contains("gitleaks")
    assert_that(cmd).contains("detect")
    assert_that(cmd).does_not_contain("--no-git")
    assert_that(cmd).contains("--config")
    assert_that(cmd).contains("--baseline-path")
    assert_that(cmd).contains("--redact")
    assert_that(cmd).contains("--max-target-megabytes")
    assert_that(cmd).contains("--report-format")
    assert_that(cmd).contains(GITLEAKS_OUTPUT_FORMAT)


# Tests for GitleaksPlugin.check method


def test_check_with_mocked_subprocess_success(
    gitleaks_plugin: GitleaksPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no secrets found.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('"""Test module with no secrets."""\n')

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            gitleaks_plugin,
            "_run_subprocess",
            return_value=(True, "[]"),
        ):
            result = gitleaks_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_secrets_found(
    gitleaks_plugin: GitleaksPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when gitleaks finds secrets.

    Args:
        gitleaks_plugin: The GitleaksPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_module.py"
    test_file.write_text('API_KEY = "AKIAIOSFODNN7EXAMPLE"\n')

    gitleaks_output = """[
        {
            "File": "test_module.py",
            "StartLine": 1,
            "StartColumn": 11,
            "EndLine": 1,
            "EndColumn": 34,
            "RuleID": "aws-access-key-id",
            "Description": "AWS Access Key ID",
            "Secret": "REDACTED",
            "Match": "AKIAIOSFODNN7EXAMPLE",
            "Fingerprint": "test_module.py:aws-access-key-id:1",
            "Entropy": 3.5
        }
    ]"""

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            gitleaks_plugin,
            "_run_subprocess",
            return_value=(True, gitleaks_output),
        ):
            result = gitleaks_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(1)
    assert_that(result.issues).is_not_none()
    assert_that(result.issues).is_length(1)


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
    test_file.write_text('"""Test module."""\n')

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
    test_file.write_text('"""Test module."""\n')

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


# Tests for GitleaksPlugin.fix method


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
    test_file.write_text('API_KEY = "secret123"\n')

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
