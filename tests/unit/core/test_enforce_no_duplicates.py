"""Tests for preventing duplicate CLI arguments from enforce and options.

This test module ensures that when Lintro's enforce tier sets a value
(like line_length), tools don't add duplicate CLI arguments from their
options. This was a bug where both enforce and options could add
--line-length, causing tools to fail with "cannot be used multiple times".
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.config.lintro_config import EnforceConfig, LintroConfig
from lintro.tools.implementations.ruff.commands import (
    build_ruff_check_command,
    build_ruff_format_command,
)
from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_ruff import RuffTool

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def isolated_tool_env() -> Generator[None]:
    """Fixture to isolate tests from project config.

    Yields:
        None
    """
    with patch.dict(os.environ, {"LINTRO_SKIP_CONFIG_INJECTION": "1"}):
        yield


def test_returns_empty_when_no_lintro_config(isolated_tool_env: None) -> None:
    """Verify empty dict when no Lintro config is loaded.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(config_path=None)
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).is_equal_to({})


def test_returns_line_length_when_enforced(isolated_tool_env: None) -> None:
    """Verify line_length is in enforced dict when set in config.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).contains_key("line_length")


def test_returns_target_python_when_enforced(isolated_tool_env: None) -> None:
    """Verify target_python is in enforced dict when set in config.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(target_python="py313"),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).contains_key("target_python")


def test_returns_both_when_both_enforced(isolated_tool_env: None) -> None:
    """Verify both settings are in enforced dict when both are set.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88, target_python="py313"),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).contains_key("line_length")
        assert_that(enforced).contains_key("target_python")


def test_returns_empty_when_enforce_has_no_values(isolated_tool_env: None) -> None:
    """Verify empty dict when enforce section exists but has no values.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).is_equal_to({})


def test_no_duplicate_line_length_when_both_enforce_and_options(
    isolated_tool_env: None,
) -> None:
    """Verify --line-length appears only once when set in both places.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    # Mock _get_lintro_config to return our test config
    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=88)
        cmd = build_ruff_check_command(tool, files=["test.py"], fix=False)
        cmd_str = " ".join(cmd)

        # Count occurrences of --line-length
        count = cmd_str.count("--line-length")
        assert_that(count).is_equal_to(
            1,
        ), f"Expected 1 --line-length, found {count} in: {cmd_str}"


def test_no_duplicate_target_version_when_both_enforce_and_options(
    isolated_tool_env: None,
) -> None:
    """Verify --target-version appears only once when set in both places.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(target_python="py313"),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(target_version="py313")
        cmd = build_ruff_check_command(tool, files=["test.py"], fix=False)
        cmd_str = " ".join(cmd)

        # Count occurrences of --target-version
        count = cmd_str.count("--target-version")
        assert_that(count).is_equal_to(
            1,
        ), f"Expected 1 --target-version, found {count}: {cmd_str}"


def test_uses_options_when_no_enforce(isolated_tool_env: None) -> None:
    """Verify options are used when enforce doesn't set the value.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(),  # No line_length enforced
        config_path=None,  # No config path means no enforce injection
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=100)
        cmd = build_ruff_check_command(tool, files=["test.py"], fix=False)
        cmd_str = " ".join(cmd)

        assert_that(cmd_str).contains("--line-length 100")


def test_uses_enforce_value_over_options(isolated_tool_env: None) -> None:
    """Verify enforce value takes precedence over options.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=100)  # Different value
        cmd = build_ruff_check_command(tool, files=["test.py"], fix=False)
        cmd_str = " ".join(cmd)

        # Should use enforce value (88), not options value (100)
        assert_that(cmd_str).contains("--line-length 88")
        assert_that(cmd_str).does_not_contain("--line-length 100")


def test_no_duplicate_line_length_with_config_args(isolated_tool_env: None) -> None:
    """Verify Black uses config_args OR options, not both.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = BlackTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=88)
        # Build args - Black should use config_args, not options
        args = tool._build_common_args()
        args_str = " ".join(args)

        # Count occurrences of --line-length
        count = args_str.count("--line-length")
        assert_that(count).is_less_than_or_equal_to(1).described_as(
            f"Expected at most 1 --line-length, found {count}: {args_str}",
        )


def test_uses_options_fallback_when_no_config_args(isolated_tool_env: None) -> None:
    """Verify Black falls back to options when no config args.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = BlackTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(),  # No enforce settings
        config_path=None,  # No Lintro config
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=100)
        args = tool._build_common_args()
        args_str = " ".join(args)

        assert_that(args_str).contains("--line-length 100")


def test_format_command_no_duplicate_line_length(isolated_tool_env: None) -> None:
    """Verify format command doesn't duplicate --line-length.

    Args:
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = RuffTool()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[attr-defined]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        tool.set_options(line_length=88)
        cmd = build_ruff_format_command(tool, files=["test.py"], check_only=False)
        cmd_str = " ".join(cmd)

        # Count occurrences of --line-length
        count = cmd_str.count("--line-length")
        assert_that(count).is_less_than_or_equal_to(1).described_as(
            f"Expected at most 1 --line-length, found {count}: {cmd_str}",
        )


@pytest.mark.parametrize(
    "tool_class",
    [RuffTool, BlackTool],
)
def test_enforced_settings_consistency(
    tool_class: type[RuffTool] | type[BlackTool],
    isolated_tool_env: None,
) -> None:
    """Verify all tools return consistent enforced settings.

    Args:
        tool_class: The tool class to test.
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = tool_class()
    test_config = LintroConfig(
        enforce=EnforceConfig(line_length=88, target_python="py313"),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[union-attr]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).contains_key("line_length")
        assert_that(enforced).contains_key("target_python")


@pytest.mark.parametrize(
    "tool_class",
    [RuffTool, BlackTool],
)
def test_no_enforced_settings_when_empty(
    tool_class: type[RuffTool] | type[BlackTool],
    isolated_tool_env: None,
) -> None:
    """Verify all tools return empty dict when nothing enforced.

    Args:
        tool_class: The tool class to test.
        isolated_tool_env: Fixture to isolate tests from project config.
    """
    tool = tool_class()
    test_config = LintroConfig(
        enforce=EnforceConfig(),
        config_path="/fake/path",
    )
    tool._lintro_config = test_config  # type: ignore[union-attr]

    with patch.object(tool, "_get_lintro_config", return_value=test_config):
        enforced = tool._get_enforced_settings()
        assert_that(enforced).is_equal_to({})
