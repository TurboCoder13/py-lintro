"""Unit tests for BaseToolPlugin Lintro config support methods.

This module contains tests for the config injection and enforcement methods
in the BaseToolPlugin class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from tests.unit.plugins.conftest import FakeToolPlugin


# =============================================================================
# BaseToolPlugin._get_lintro_config Tests
# =============================================================================


def test_get_lintro_config_returns_config(fake_tool_plugin: FakeToolPlugin) -> None:
    """Verify _get_lintro_config returns the Lintro configuration object.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    mock_config = MagicMock()
    mock_config.enforce = {"line_length": 100}

    with patch(
        "lintro.tools.core.config_injection._get_lintro_config",
        return_value=mock_config,
    ):
        result = fake_tool_plugin._get_lintro_config()

        assert_that(result).is_equal_to(mock_config)
        assert_that(result.enforce).is_equal_to({"line_length": 100})


def test_get_lintro_config_returns_none_when_not_found(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_lintro_config returns None when no config is found.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with patch(
        "lintro.tools.core.config_injection._get_lintro_config",
        return_value=None,
    ):
        result = fake_tool_plugin._get_lintro_config()

        assert_that(result).is_none()


# =============================================================================
# BaseToolPlugin._get_enforced_settings Tests
# =============================================================================


def test_get_enforced_settings_returns_settings(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_enforced_settings returns enforced settings dictionary.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    expected_settings = {"line_length": 100, "indent_size": 4}

    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_enforced_settings",
            return_value=expected_settings,
        ),
    ):
        result = fake_tool_plugin._get_enforced_settings()

        assert_that(result).is_equal_to(expected_settings)
        assert_that(result).contains_key("line_length")
        assert_that(result).contains_key("indent_size")


def test_get_enforced_settings_returns_empty_dict_when_no_enforcement(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_enforced_settings returns empty dict when no enforcement.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_enforced_settings",
            return_value={},
        ),
    ):
        result = fake_tool_plugin._get_enforced_settings()

        assert_that(result).is_empty()


# =============================================================================
# BaseToolPlugin._get_enforce_cli_args Tests
# =============================================================================


def test_get_enforce_cli_args_returns_args(fake_tool_plugin: FakeToolPlugin) -> None:
    """Verify _get_enforce_cli_args returns CLI arguments for enforcement.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    expected_args = ["--line-length", "100", "--indent", "4"]

    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_enforce_cli_args",
            return_value=expected_args,
        ),
    ):
        result = fake_tool_plugin._get_enforce_cli_args()

        assert_that(result).is_equal_to(expected_args)
        assert_that(result).is_length(4)
        assert_that(result).contains("--line-length", "100")


def test_get_enforce_cli_args_returns_empty_list_when_no_args(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_enforce_cli_args returns empty list when no enforcement args.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_enforce_cli_args",
            return_value=[],
        ),
    ):
        result = fake_tool_plugin._get_enforce_cli_args()

        assert_that(result).is_empty()


# =============================================================================
# BaseToolPlugin._get_defaults_config_args Tests
# =============================================================================


def test_get_defaults_config_args_returns_args(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_defaults_config_args returns default config arguments.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    expected_args = ["--config", "defaults"]

    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_defaults_config_args",
            return_value=expected_args,
        ),
    ):
        result = fake_tool_plugin._get_defaults_config_args()

        assert_that(result).is_equal_to(expected_args)
        assert_that(result).is_length(2)


def test_get_defaults_config_args_returns_empty_list_when_no_defaults(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _get_defaults_config_args returns empty list when no defaults.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._get_defaults_config_args",
            return_value=[],
        ),
    ):
        result = fake_tool_plugin._get_defaults_config_args()

        assert_that(result).is_empty()


# =============================================================================
# BaseToolPlugin._should_use_lintro_config Tests
# =============================================================================


@pytest.mark.parametrize(
    ("should_use", "expected"),
    [
        pytest.param(True, True, id="returns_true"),
        pytest.param(False, False, id="returns_false"),
    ],
)
def test_should_use_lintro_config(
    fake_tool_plugin: FakeToolPlugin,
    should_use: bool,
    expected: bool,
) -> None:
    """Verify _should_use_lintro_config returns the expected boolean.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
        should_use: The value to mock for should_use_lintro_config.
        expected: The expected return value.
    """
    with patch(
        "lintro.tools.core.config_injection._should_use_lintro_config",
        return_value=should_use,
    ):
        result = fake_tool_plugin._should_use_lintro_config()

        assert_that(result).is_equal_to(expected)


# =============================================================================
# BaseToolPlugin._build_config_args Tests
# =============================================================================


def test_build_config_args_returns_args(fake_tool_plugin: FakeToolPlugin) -> None:
    """Verify _build_config_args returns built configuration arguments.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    expected_args = ["--config-arg", "--another-arg"]

    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._build_config_args",
            return_value=expected_args,
        ),
    ):
        result = fake_tool_plugin._build_config_args()

        assert_that(result).is_equal_to(expected_args)
        assert_that(result).is_length(2)


def test_build_config_args_returns_empty_list_when_no_config(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _build_config_args returns empty list when no config args.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._build_config_args",
            return_value=[],
        ),
    ):
        result = fake_tool_plugin._build_config_args()

        assert_that(result).is_empty()


def test_build_config_args_combines_multiple_sources(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify _build_config_args can combine args from multiple config sources.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    combined_args = [
        "--line-length",
        "100",
        "--config",
        "defaults",
        "--strict",
    ]

    with (
        patch(
            "lintro.tools.core.config_injection._get_lintro_config",
            return_value=MagicMock(),
        ),
        patch(
            "lintro.tools.core.config_injection._build_config_args",
            return_value=combined_args,
        ),
    ):
        result = fake_tool_plugin._build_config_args()

        assert_that(result).is_length(5)
        assert_that(result).contains("--line-length", "100", "--strict")
