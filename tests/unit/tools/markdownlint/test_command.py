"""Tests for _get_markdownlint_command method."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_get_markdownlint_command_with_npx(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Get command uses npx when available.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with patch("shutil.which", return_value="/usr/local/bin/npx"):
        cmd = markdownlint_plugin._get_markdownlint_command()
        assert_that(cmd).is_equal_to(["npx", "markdownlint-cli2"])


def test_get_markdownlint_command_without_npx(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Get command falls back to direct executable when npx not available.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with patch("shutil.which", return_value=None):
        cmd = markdownlint_plugin._get_markdownlint_command()
        assert_that(cmd).is_equal_to(["markdownlint-cli2"])
