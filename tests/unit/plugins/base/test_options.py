"""Unit tests for BaseToolPlugin set_options and _setup_defaults methods."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.plugins.base import DEFAULT_EXCLUDE_PATTERNS

if TYPE_CHECKING:
    from tests.unit.plugins.conftest import FakeToolPlugin


# =============================================================================
# BaseToolPlugin.set_options Tests
# =============================================================================


@pytest.mark.parametrize(
    ("timeout_value", "expected"),
    [
        pytest.param(60, 60.0, id="integer_timeout"),
        pytest.param(45.5, 45.5, id="float_timeout"),
        pytest.param(0, 0.0, id="zero_timeout"),
    ],
)
def test_set_options_timeout_valid_values(
    fake_tool_plugin: FakeToolPlugin,
    timeout_value: int | float,
    expected: float,
) -> None:
    """Verify valid timeout values are accepted and stored correctly.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
        timeout_value: The timeout value to set.
        expected: The expected timeout value after setting.
    """
    fake_tool_plugin.set_options(timeout=timeout_value)

    assert_that(fake_tool_plugin.options.get("timeout")).is_equal_to(expected)


def test_set_options_timeout_none(fake_tool_plugin: FakeToolPlugin) -> None:
    """Verify timeout can be set to None.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    fake_tool_plugin.set_options(timeout=None)

    assert_that(fake_tool_plugin.options.get("timeout")).is_none()


def test_set_options_timeout_invalid_raises_value_error(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify invalid timeout type raises ValueError with descriptive message.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with pytest.raises(ValueError, match="Timeout must be a number"):
        fake_tool_plugin.set_options(timeout="invalid")


def test_set_options_exclude_patterns_valid(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify valid exclude patterns list is accepted and stored.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    patterns = ["*.log", "*.tmp"]
    fake_tool_plugin.set_options(exclude_patterns=patterns)

    assert_that(fake_tool_plugin.exclude_patterns).is_equal_to(patterns)


def test_set_options_exclude_patterns_invalid_raises_value_error(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify non-list exclude patterns raises ValueError.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with pytest.raises(ValueError, match="Exclude patterns must be a list"):
        fake_tool_plugin.set_options(exclude_patterns="*.log")


def test_set_options_include_venv_valid(fake_tool_plugin: FakeToolPlugin) -> None:
    """Verify valid boolean include_venv is accepted.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    fake_tool_plugin.set_options(include_venv=True)

    assert_that(fake_tool_plugin.include_venv).is_true()


def test_set_options_include_venv_invalid_raises_value_error(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify non-boolean include_venv raises ValueError.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    with pytest.raises(ValueError, match="Include venv must be a boolean"):
        fake_tool_plugin.set_options(include_venv="yes")


# =============================================================================
# BaseToolPlugin._setup_defaults Tests
# =============================================================================


def test_setup_defaults_adds_default_exclude_patterns(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify default exclude patterns are added to plugin's exclude_patterns.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    for pattern in DEFAULT_EXCLUDE_PATTERNS:
        assert_that(pattern in fake_tool_plugin.exclude_patterns).is_true()

    assert_that(fake_tool_plugin.exclude_patterns).is_not_empty()


def test_setup_defaults_adds_lintro_ignore_patterns(tmp_path: Path) -> None:
    """Verify patterns from .lintro-ignore file are added to exclude_patterns.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    from tests.unit.plugins.conftest import FakeToolPlugin

    ignore_file = tmp_path / ".lintro-ignore"
    ignore_file.write_text("custom_pattern\n# comment\n\nother_pattern\n")

    with patch(
        "lintro.plugins.file_discovery.find_lintro_ignore",
        return_value=ignore_file,
    ):
        plugin = FakeToolPlugin()

        assert_that("custom_pattern" in plugin.exclude_patterns).is_true()
        assert_that("other_pattern" in plugin.exclude_patterns).is_true()


def test_setup_defaults_handles_lintro_ignore_read_error_gracefully() -> None:
    """Verify .lintro-ignore read errors are handled without raising."""
    from tests.unit.plugins.conftest import FakeToolPlugin

    with patch(
        "lintro.plugins.file_discovery.find_lintro_ignore",
        side_effect=PermissionError("Access denied"),
    ):
        plugin = FakeToolPlugin()

        # Should not raise, just log debug
        assert_that(plugin.exclude_patterns).is_not_empty()


def test_setup_defaults_sets_default_timeout_from_definition(
    fake_tool_plugin: FakeToolPlugin,
) -> None:
    """Verify default timeout is set from tool definition.

    Args:
        fake_tool_plugin: The fake tool plugin instance to test.
    """
    assert_that(fake_tool_plugin.options.get("timeout")).is_equal_to(30)
