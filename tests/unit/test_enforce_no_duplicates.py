"""Tests for preventing duplicate CLI arguments from enforce and options.

This test module ensures that when Lintro's enforce tier sets a value
(like line_length), tools don't add duplicate CLI arguments from their
options. This was a bug where both enforce and options could add
--line-length, causing tools to fail with "cannot be used multiple times".
"""

import os
from unittest.mock import patch

import pytest

from lintro.config.lintro_config import EnforceConfig, LintroConfig
from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_ruff import RuffTool


@pytest.fixture
def isolated_tool_env():
    """Fixture to isolate tests from project config.

    Yields:
        None
    """
    with patch.dict(os.environ, {"LINTRO_SKIP_CONFIG_INJECTION": "1"}):
        yield


class TestGetEnforcedSettings:
    """Tests for _get_enforced_settings() method."""

    def test_returns_empty_when_no_lintro_config(self) -> None:
        """Verify empty set when no Lintro config is loaded."""
        tool = RuffTool()
        test_config = LintroConfig(config_path=None)
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert enforced == set()

    def test_returns_line_length_when_enforced(self) -> None:
        """Verify line_length is in enforced set when set in config."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert "line_length" in enforced

    def test_returns_target_python_when_enforced(self) -> None:
        """Verify target_python is in enforced set when set in config."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(target_python="py313"),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert "target_python" in enforced

    def test_returns_both_when_both_enforced(self) -> None:
        """Verify both settings are in enforced set when both are set."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88, target_python="py313"),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert "line_length" in enforced
            assert "target_python" in enforced

    def test_returns_empty_when_enforce_has_no_values(self) -> None:
        """Verify empty set when enforce section exists but has no values."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert enforced == set()


class TestRuffNoDuplicateCliArgs:
    """Tests that Ruff doesn't generate duplicate CLI arguments."""

    def test_no_duplicate_line_length_when_both_enforce_and_options(self) -> None:
        """Verify --line-length appears only once when set in both places."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        # Mock _get_lintro_config to return our test config
        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=88)
            cmd = tool._build_check_command(files=["test.py"], fix=False)
            cmd_str = " ".join(cmd)

            # Count occurrences of --line-length
            count = cmd_str.count("--line-length")
            assert count == 1, f"Expected 1 --line-length, found {count} in: {cmd_str}"

    def test_no_duplicate_target_version_when_both_enforce_and_options(self) -> None:
        """Verify --target-version appears only once when set in both places."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(target_python="py313"),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(target_version="py313")
            cmd = tool._build_check_command(files=["test.py"], fix=False)
            cmd_str = " ".join(cmd)

            # Count occurrences of --target-version
            count = cmd_str.count("--target-version")
            assert count == 1, f"Expected 1 --target-version, found {count}: {cmd_str}"

    def test_uses_options_when_no_enforce(self) -> None:
        """Verify options are used when enforce doesn't set the value."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(),  # No line_length enforced
            config_path=None,  # No config path means no enforce injection
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=100)
            cmd = tool._build_check_command(files=["test.py"], fix=False)
            cmd_str = " ".join(cmd)

            assert "--line-length 100" in cmd_str

    def test_uses_enforce_value_over_options(self) -> None:
        """Verify enforce value takes precedence over options."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=100)  # Different value
            cmd = tool._build_check_command(files=["test.py"], fix=False)
            cmd_str = " ".join(cmd)

            # Should use enforce value (88), not options value (100)
            assert "--line-length 88" in cmd_str
            assert "--line-length 100" not in cmd_str


class TestBlackNoDuplicateCliArgs:
    """Tests that Black doesn't generate duplicate CLI arguments."""

    def test_no_duplicate_line_length_with_config_args(self) -> None:
        """Verify Black uses config_args OR options, not both."""
        tool = BlackTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=88)
            # Build args - Black should use config_args, not options
            args = tool._build_common_args()
            args_str = " ".join(args)

            # Count occurrences of --line-length
            count = args_str.count("--line-length")
            assert (
                count <= 1
            ), f"Expected at most 1 --line-length, found {count}: {args_str}"

    def test_uses_options_fallback_when_no_config_args(self) -> None:
        """Verify Black falls back to options when no config args."""
        tool = BlackTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(),  # No enforce settings
            config_path=None,  # No Lintro config
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=100)
            args = tool._build_common_args()
            args_str = " ".join(args)

            assert "--line-length 100" in args_str


class TestRuffFormatCommandNoDuplicates:
    """Tests that Ruff format command doesn't generate duplicates."""

    def test_format_command_no_duplicate_line_length(self) -> None:
        """Verify format command doesn't duplicate --line-length."""
        tool = RuffTool()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            tool.set_options(line_length=88)
            cmd = tool._build_format_command(files=["test.py"], check_only=False)
            cmd_str = " ".join(cmd)

            # Count occurrences of --line-length
            count = cmd_str.count("--line-length")
            assert (
                count <= 1
            ), f"Expected at most 1 --line-length, found {count}: {cmd_str}"


class TestEnforcedSettingsAcrossTools:
    """Test that _get_enforced_settings works consistently across tools."""

    @pytest.mark.parametrize(
        "tool_class",
        [RuffTool, BlackTool],
    )
    def test_enforced_settings_consistency(self, tool_class) -> None:
        """Verify all tools return consistent enforced settings.

        Args:
            tool_class: The tool class to test.
        """
        tool = tool_class()
        test_config = LintroConfig(
            enforce=EnforceConfig(line_length=88, target_python="py313"),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert "line_length" in enforced
            assert "target_python" in enforced

    @pytest.mark.parametrize(
        "tool_class",
        [RuffTool, BlackTool],
    )
    def test_no_enforced_settings_when_empty(self, tool_class) -> None:
        """Verify all tools return empty set when nothing enforced.

        Args:
            tool_class: The tool class to test.
        """
        tool = tool_class()
        test_config = LintroConfig(
            enforce=EnforceConfig(),
            config_path="/fake/path",
        )
        tool._lintro_config = test_config

        with patch.object(tool, "_get_lintro_config", return_value=test_config):
            enforced = tool._get_enforced_settings()
            assert enforced == set()
