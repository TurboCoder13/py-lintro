"""Tests for BiomePlugin.fix method."""

from __future__ import annotations

import pathlib
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.enums.tool_name import ToolName
from lintro.parsers.biome.biome_issue import BiomeIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.biome import BiomePlugin


def test_fix_success_all_fixed(biome_plugin: BiomePlugin, tmp_path: str) -> None:
    """Fix returns success when all issues fixed.

    Args:
        biome_plugin: The BiomePlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = pathlib.Path(tmp_path) / "test.js"
    test_file.write_text("var x = 1;\n")

    initial_output = """{
        "diagnostics": [
            {
                "category": "lint/style/noVar",
                "severity": "error",
                "description": "Use let or const instead of var",
                "location": {
                    "path": {"file": "test.js"},
                    "span": [0, 3],
                    "sourceCode": "var"
                },
                "tags": ["fixable"]
            }
        ]
    }"""
    final_output = '{"diagnostics": []}'

    call_count = 0

    def mock_run_subprocess(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (False, initial_output)
        elif call_count == 2:
            return (True, "")
        else:
            return (True, final_output)

    with (
        patch.object(biome_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            biome_plugin,
            "_run_subprocess",
            side_effect=mock_run_subprocess,
        ),
        patch.object(biome_plugin, "_get_executable_command", return_value=["biome"]),
        patch.object(biome_plugin, "_build_config_args", return_value=[]),
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.early_result = None
        mock_ctx.timeout = 30
        mock_ctx.cwd = str(tmp_path)
        mock_ctx.rel_files = ["test.js"]
        mock_ctx.files = [str(test_file)]
        mock_prepare.return_value = mock_ctx

        result = biome_plugin.fix([str(test_file)], {})

        assert_that(result.name).is_equal_to(ToolName.BIOME)
        assert_that(result.success).is_true()
        assert_that(result.initial_issues_count).is_equal_to(1)
        assert_that(result.fixed_issues_count).is_equal_to(1)
        assert_that(result.remaining_issues_count).is_equal_to(0)


def test_fix_partial_fix(biome_plugin: BiomePlugin, tmp_path: str) -> None:
    """Fix returns remaining issues when not all can be fixed.

    Args:
        biome_plugin: The BiomePlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = pathlib.Path(tmp_path) / "test.js"
    test_file.write_text("var x = 1;\n")

    initial_output = """{
        "diagnostics": [
            {
                "category": "lint/style/noVar",
                "severity": "error",
                "description": "Use let or const instead of var",
                "location": {
                    "path": {"file": "test.js"},
                    "span": [0, 3],
                    "sourceCode": "var"
                },
                "tags": ["fixable"]
            },
            {
                "category": "lint/correctness/noUnusedVariables",
                "severity": "warning",
                "description": "Unused variable x",
                "location": {
                    "path": {"file": "test.js"},
                    "span": [4, 5],
                    "sourceCode": "x"
                },
                "tags": []
            }
        ]
    }"""
    final_output = """{
        "diagnostics": [
            {
                "category": "lint/correctness/noUnusedVariables",
                "severity": "warning",
                "description": "Unused variable x",
                "location": {
                    "path": {"file": "test.js"},
                    "span": [4, 5],
                    "sourceCode": "x"
                },
                "tags": []
            }
        ]
    }"""

    call_count = 0

    def mock_run_subprocess(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (False, initial_output)
        elif call_count == 2:
            return (True, "")
        else:
            return (False, final_output)

    with (
        patch.object(biome_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            biome_plugin,
            "_run_subprocess",
            side_effect=mock_run_subprocess,
        ),
        patch.object(biome_plugin, "_get_executable_command", return_value=["biome"]),
        patch.object(biome_plugin, "_build_config_args", return_value=[]),
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.early_result = None
        mock_ctx.timeout = 30
        mock_ctx.cwd = str(tmp_path)
        mock_ctx.rel_files = ["test.js"]
        mock_ctx.files = [str(test_file)]
        mock_prepare.return_value = mock_ctx

        result = biome_plugin.fix([str(test_file)], {})

        assert_that(result.success).is_false()
        assert_that(result.initial_issues_count).is_equal_to(2)
        assert_that(result.fixed_issues_count).is_equal_to(1)
        assert_that(result.remaining_issues_count).is_equal_to(1)


def test_fix_timeout_on_initial_check(
    biome_plugin: BiomePlugin,
    tmp_path: str,
) -> None:
    """Fix handles timeout on initial check.

    Args:
        biome_plugin: The BiomePlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    from lintro.models.core.tool_result import ToolResult

    test_file = pathlib.Path(tmp_path) / "test.js"
    test_file.write_text("const x = 1;\n")

    timeout_result = ToolResult(
        name="biome",
        success=False,
        output="Biome execution timed out (30s limit exceeded).",
        issues_count=1,
        issues=[
            BiomeIssue(
                file="execution",
                line=1,
                column=1,
                code="TIMEOUT",
                message="Biome execution timed out",
                severity="error",
                fixable=False,
            ),
        ],
        initial_issues_count=1,
        fixed_issues_count=0,
        remaining_issues_count=1,
    )

    with (
        patch.object(biome_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            biome_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["biome"], timeout=30),
        ),
        patch.object(biome_plugin, "_get_executable_command", return_value=["biome"]),
        patch.object(biome_plugin, "_build_config_args", return_value=[]),
        patch.object(
            biome_plugin,
            "_create_timeout_result",
            return_value=timeout_result,
        ),
    ):
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.early_result = None
        mock_ctx.timeout = 30
        mock_ctx.cwd = str(tmp_path)
        mock_ctx.rel_files = ["test.js"]
        mock_ctx.files = [str(test_file)]
        mock_prepare.return_value = mock_ctx

        result = biome_plugin.fix([str(test_file)], {})

        assert_that(result.success).is_false()
        assert_that(result.output).contains("timed out")
