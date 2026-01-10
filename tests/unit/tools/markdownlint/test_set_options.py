"""Tests for MarkdownlintPlugin.set_options method."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_set_options_timeout(markdownlint_plugin: MarkdownlintPlugin) -> None:
    """Set timeout option.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    markdownlint_plugin.set_options(timeout=60)
    assert_that(markdownlint_plugin.options.get("timeout")).is_equal_to(60)


def test_set_options_line_length(markdownlint_plugin: MarkdownlintPlugin) -> None:
    """Set line_length option.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    markdownlint_plugin.set_options(line_length=100)
    assert_that(markdownlint_plugin.options.get("line_length")).is_equal_to(100)


def test_set_options_no_options(markdownlint_plugin: MarkdownlintPlugin) -> None:
    """Handle no options set - line_length defaults from central config.

    When set_options() is called without arguments, line_length is fetched
    from the central configuration (pyproject.toml or similar), so the
    options dictionary may be updated with this value.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    initial_timeout = markdownlint_plugin.options.get("timeout")
    markdownlint_plugin.set_options()
    # Timeout should remain unchanged when not provided
    assert_that(markdownlint_plugin.options.get("timeout")).is_equal_to(initial_timeout)
    # line_length may be set from central config, so we just verify it's a valid int
    line_length = markdownlint_plugin.options.get("line_length")
    if line_length is not None:
        assert_that(line_length).is_instance_of(int)
        assert_that(line_length).is_greater_than(0)


def test_set_options_invalid_timeout_type(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for invalid timeout type.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="timeout must be an integer"):
        markdownlint_plugin.set_options(timeout="30")  # type: ignore[arg-type]


def test_set_options_invalid_timeout_value(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for invalid timeout value.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="timeout must be positive"):
        markdownlint_plugin.set_options(timeout=0)


def test_set_options_negative_timeout(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for negative timeout.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="timeout must be positive"):
        markdownlint_plugin.set_options(timeout=-1)


def test_set_options_invalid_line_length_type(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for invalid line_length type.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="line_length must be an integer"):
        markdownlint_plugin.set_options(line_length="80")  # type: ignore[arg-type]


def test_set_options_invalid_line_length_value(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for invalid line_length value.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="line_length must be positive"):
        markdownlint_plugin.set_options(line_length=0)


def test_set_options_negative_line_length(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Raise ValueError for negative line_length.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(ValueError, match="line_length must be positive"):
        markdownlint_plugin.set_options(line_length=-1)
