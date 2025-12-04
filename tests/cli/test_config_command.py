"""Tests for the lintro config CLI command."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lintro.cli import cli


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing.

    Returns:
        CliRunner: A Click test runner instance.
    """
    return CliRunner()


class TestConfigCommand:
    """Tests for the config CLI command."""

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_runs(
        self,
        mock_injectable: MagicMock,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Config command runs successfully.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        # Setup mocks
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {
            "ruff": MagicMock(
                tool_name="ruff",
                is_injectable=True,
                effective_config={"line_length": 88},
                lintro_tool_config={},
                native_config={},
            ),
        }
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = ["ruff"]
        mock_priority.return_value = 20
        mock_injectable.return_value = True

        result = cli_runner.invoke(cli, ["config"])

        # Should succeed (exit code 0)
        assert result.exit_code == 0

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_shows_line_length(
        self,
        mock_injectable: MagicMock,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Config command displays line length.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = []

        result = cli_runner.invoke(cli, ["config"])

        assert "88" in result.output or "line_length" in result.output.lower()

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_command_shows_warnings(
        self,
        mock_injectable: MagicMock,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Config command displays configuration warnings.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = ["prettier: Native config has printWidth=100"]
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = []

        result = cli_runner.invoke(cli, ["config"])

        assert "prettier" in result.output.lower() or "warning" in result.output.lower()

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_config_alias_works(
        self,
        mock_injectable: MagicMock,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Config command alias 'cfg' works and executes the command.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = []

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


class TestConfigCommandJsonOutput:
    """Tests for JSON output mode of config command."""

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    def test_json_output_is_valid_json(
        self,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output is valid JSON.

        Args:
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {
            "ruff": MagicMock(
                tool_name="ruff",
                is_injectable=True,
                effective_config={"line_length": 88},
                lintro_tool_config={},
                native_config={},
                warnings=[],
            ),
        }
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = ["ruff"]
        mock_priority.return_value = 20

        result = cli_runner.invoke(cli, ["config", "--json"])

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "global_settings" in data
        assert "tool_configs" in data

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    def test_json_output_includes_line_length(
        self,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes line length in global settings.

        Args:
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = []
        mock_priority.return_value = 50

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert data["global_settings"]["line_length"] == 88

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    def test_json_output_includes_tool_order(
        self,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes tool execution order.

        Args:
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = ["prettier", "ruff"]
        mock_priority.side_effect = lambda t: {"prettier": 10, "ruff": 20}.get(t, 50)

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert "tool_execution_order" in data
        assert data["tool_execution_order"][0]["tool"] == "prettier"
        assert data["tool_execution_order"][1]["tool"] == "ruff"

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    def test_json_output_includes_warnings(
        self,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """JSON output includes configuration warnings.

        Args:
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {}
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = ["prettier: Native config differs"]
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = []

        result = cli_runner.invoke(cli, ["config", "--json"])

        data = json.loads(result.output)
        assert "warnings" in data
        assert len(data["warnings"]) > 0
        assert "prettier" in data["warnings"][0]


class TestConfigCommandVerbose:
    """Tests for verbose mode of config command."""

    @patch("lintro.cli_utils.commands.config.UnifiedConfigManager")
    @patch("lintro.cli_utils.commands.config.validate_config_consistency")
    @patch("lintro.cli_utils.commands.config.get_tool_order_config")
    @patch("lintro.cli_utils.commands.config.get_effective_line_length")
    @patch("lintro.cli_utils.commands.config.get_ordered_tools")
    @patch("lintro.cli_utils.commands.config.get_tool_priority")
    @patch("lintro.cli_utils.commands.config.is_tool_injectable")
    def test_verbose_shows_native_config(
        self,
        mock_injectable: MagicMock,
        mock_priority: MagicMock,
        mock_ordered: MagicMock,
        mock_line_length: MagicMock,
        mock_order_config: MagicMock,
        mock_validate: MagicMock,
        mock_manager: MagicMock,
        cli_runner: CliRunner,
    ) -> None:
        """Verbose mode shows native config column.

        Args:
            mock_injectable: Mock for is_tool_injectable function.
            mock_priority: Mock for get_tool_priority function.
            mock_ordered: Mock for get_ordered_tools function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_order_config: Mock for get_tool_order_config function.
            mock_validate: Mock for validate_config_consistency function.
            mock_manager: Mock for UnifiedConfigManager class.
            cli_runner: Click test runner instance.
        """
        mock_manager_instance = MagicMock()
        mock_manager_instance.tool_configs = {
            "prettier": MagicMock(
                tool_name="prettier",
                is_injectable=False,
                effective_config={},
                lintro_tool_config={},
                native_config={"printWidth": 100},
            ),
        }
        mock_manager.return_value = mock_manager_instance
        mock_validate.return_value = []
        mock_order_config.return_value = {"strategy": "priority"}
        mock_line_length.return_value = 88
        mock_ordered.return_value = ["prettier"]
        mock_priority.return_value = 10
        mock_injectable.return_value = False

        result = cli_runner.invoke(cli, ["config", "--verbose"])

        assert result.exit_code == 0
        # Verbose should show Native Config column
        assert "Native" in result.output or "native" in result.output.lower()
