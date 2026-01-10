"""Tests for YamllintPlugin._process_single_file method."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


def test_process_single_file_success(yamllint_plugin: YamllintPlugin) -> None:
    """Process single file successfully with no issues.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_get_executable_command") as mock_exec,
        patch.object(yamllint_plugin, "_run_subprocess") as mock_run,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch("os.path.abspath", side_effect=lambda p: f"/abs/{p}"),
        patch("os.path.dirname", return_value="/abs"),
    ):
        mock_exec.return_value = ["yamllint"]
        mock_run.return_value = (True, "")
        mock_config.return_value = None

        results = {
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "timeout_count": 0,
            "execution_failures": 0,
            "total_issues": 0,
        }

        yamllint_plugin._process_single_file(
            file_path="test.yml",
            timeout=15,
            results=results,
        )

        assert_that(results["all_success"]).is_true()
        assert_that(results["total_issues"]).is_equal_to(0)


def test_process_single_file_with_issues(yamllint_plugin: YamllintPlugin) -> None:
    """Process single file with issues found.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_get_executable_command") as mock_exec,
        patch.object(yamllint_plugin, "_run_subprocess") as mock_run,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch("os.path.abspath", side_effect=lambda p: f"/abs/{p}"),
        patch("os.path.dirname", return_value="/abs"),
    ):
        mock_exec.return_value = ["yamllint"]
        mock_run.return_value = (
            False,
            "test.yml:5:1: [error] trailing spaces (trailing-spaces)",
        )
        mock_config.return_value = None

        results = {
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "timeout_count": 0,
            "execution_failures": 0,
            "total_issues": 0,
        }

        yamllint_plugin._process_single_file(
            file_path="test.yml",
            timeout=15,
            results=results,
        )

        assert_that(results["all_success"]).is_false()
        assert_that(results["total_issues"]).is_equal_to(1)
        assert_that(results["all_issues"]).is_length(1)


def test_process_single_file_timeout(yamllint_plugin: YamllintPlugin) -> None:
    """Process single file handles timeout.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    with (
        patch.object(yamllint_plugin, "_get_executable_command") as mock_exec,
        patch.object(yamllint_plugin, "_run_subprocess") as mock_run,
        patch.object(yamllint_plugin, "_find_yamllint_config") as mock_config,
        patch("os.path.abspath", side_effect=lambda p: f"/abs/{p}"),
        patch("os.path.dirname", return_value="/abs"),
    ):
        mock_exec.return_value = ["yamllint"]
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yamllint", timeout=15)
        mock_config.return_value = None

        results = {
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "timeout_count": 0,
            "execution_failures": 0,
            "total_issues": 0,
        }

        yamllint_plugin._process_single_file(
            file_path="test.yml",
            timeout=15,
            results=results,
        )

        assert_that(results["all_success"]).is_false()
        assert_that(results["timeout_count"]).is_equal_to(1)
        assert_that(results["skipped_files"]).contains("test.yml")
