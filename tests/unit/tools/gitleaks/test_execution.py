"""Unit tests for gitleaks plugin check method execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.definitions.gitleaks import GitleaksPlugin


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
