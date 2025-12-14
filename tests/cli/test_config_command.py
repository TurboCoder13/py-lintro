"""Tests for the lintro config CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lintro.cli import cli
from lintro.config.lintro_config import (
    EnforceConfig,
    ExecutionConfig,
    LintroConfig,
    ToolConfig,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing.

    Returns:
        CliRunner: A Click test runner instance.
    """
    return CliRunner()


@pytest.fixture
def mock_config() -> LintroConfig:
    """Create a mock LintroConfig for testing.

    Returns:
        LintroConfig: A configured LintroConfig instance.
    """
    return LintroConfig(
        execution=ExecutionConfig(
            enabled_tools=[],
            tool_order="priority",
            fail_fast=False,
        ),
        enforce=EnforceConfig(
            line_length=88,
            target_python="py313",
        ),
        tools={
            "ruff": ToolConfig(enabled=True),
            "prettier": ToolConfig(enabled=True),
        },
        config_path="/path/to/.lintro-config.yaml",
    )


class TestConfigCommand:
    """Tests for the config CLI command."""

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_runs(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command runs successfully.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config"])

        # Should succeed (exit code 0)
        assert result.exit_code == 0

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_shows_line_length(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command displays line length.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config"])

        assert "88" in result.output or "line_length" in result.output.lower()

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_shows_warnings(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command displays configuration warnings.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = ["prettier: Native config has printWidth=100"]
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config"])

        assert "prettier" in result.output.lower() or "warning" in result.output.lower()

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_alias_works(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command alias 'cfg' works and executes the command.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        # Test alias without --help to verify actual execution
        result = cli_runner.invoke(cli, ["cfg"])

        assert result.exit_code == 0
        # Verify it produces the same output as the non-aliased command
        assert "88" in result.output or "line_length" in result.output.lower()

        # Also verify the non-aliased command for comparison
        result_normal = cli_runner.invoke(cli, ["config"])
        assert result_normal.exit_code == 0
        # Both should produce similar output structure
        assert len(result.output) > 0
        assert len(result_normal.output) > 0

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_shows_config_source(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command displays the config source file.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        # Should show the config source path
        assert (
            ".lintro-config.yaml" in result.output or "Config Source" in result.output
        )

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_exports_yaml(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Config command exports effective config to YAML.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                cli,
                ["config", "--export", ".lintro-config.yaml"],
            )

            assert result.exit_code == 0
            export_file = Path(".lintro-config.yaml")
            assert export_file.exists()
            content = export_file.read_text(encoding="utf-8")
            assert "enforce:" in content
            assert "py313" in content


class TestConfigCommandJsonOutput:
    """Tests for JSON output mode of config command."""

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_json_output_is_valid_json(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output is valid JSON.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config", "--json"])

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "global_settings" in data
        assert "tool_configs" in data

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_json_output_includes_line_length(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes line length in global settings.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert data["global_settings"]["line_length"] == 88

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_json_output_includes_tool_order(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes tool execution order.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert "tool_execution_order" in data
        # Should have tools in priority order (prettier before ruff)
        tool_names = [t["tool"] for t in data["tool_execution_order"]]
        assert "prettier" in tool_names
        assert "ruff" in tool_names
        # Verify prettier comes before ruff (lower priority = runs first)
        assert tool_names.index("prettier") < tool_names.index("ruff")

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_json_output_includes_warnings(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes configuration warnings.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = ["prettier: Native config differs"]
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert "warnings" in data
        assert len(data["warnings"]) > 0
        assert "prettier" in data["warnings"][0]

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_json_output_includes_config_source(
        self,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes config_source field.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert "config_source" in data
        assert ".lintro-config.yaml" in data["config_source"]


class TestConfigCommandVerbose:
    """Tests for verbose mode of config command."""

    @patch("lintro.cli_utils.commands.config.get_config")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    @patch("lintro.cli_utils.commands.config._load_native_tool_config")
    def test_verbose_shows_native_config(
        self,
        mock_native_config: MagicMock,
        mock_injectable: MagicMock,
        mock_validate: MagicMock,
        mock_get_config: MagicMock,
        mock_config: LintroConfig,
        cli_runner: CliRunner,
    ) -> None:
        """Verbose mode shows native config column.

        Args:
            mock_native_config: Mock for _load_native_tool_config function.
            mock_injectable: Mock for is_tool_injectable function.
            mock_validate: Mock for validate_config_consistency function.
            mock_get_config: Mock for get_config function.
            mock_config: Mock LintroConfig instance.
            cli_runner: Click test runner instance.
        """
        mock_get_config.return_value = mock_config
        mock_validate.return_value = []
        mock_injectable.return_value = False
        mock_native_config.return_value = {"printWidth": 100}

        result = cli_runner.invoke(cli, ["config", "--verbose"])

        assert result.exit_code == 0
        # Verbose should show Native Config column
        assert "Native" in result.output or "native" in result.output.lower()
