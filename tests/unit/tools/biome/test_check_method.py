"""Tests for BiomePlugin.check method."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.enums.tool_name import ToolName
from lintro.parsers.biome.biome_issue import BiomeIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.biome import BiomePlugin


def test_check_with_issues(biome_plugin: BiomePlugin, tmp_path: str) -> None:
    """Check returns issues when found.

    Args:
        biome_plugin: The BiomePlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = pathlib.Path(tmp_path) / "test.js"
    test_file.write_text("var x = 1;\n")

    mock_output = """{
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
    mock_result = (False, mock_output)

    with (
        patch.object(biome_plugin, "_prepare_execution") as mock_prepare,
        patch.object(biome_plugin, "_run_subprocess", return_value=mock_result),
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

        result = biome_plugin.check([str(test_file)], {})

        assert_that(result.name).is_equal_to(ToolName.BIOME)
        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(1)
        assert_that(result.issues).is_not_none()
        issue = cast(BiomeIssue, result.issues[0])  # type: ignore[index]  # validated via is_not_none
        assert_that(issue.code).is_equal_to("lint/style/noVar")
