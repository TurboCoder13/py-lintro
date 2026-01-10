"""Tests for MarkdownlintPlugin.fix method."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_fix_error_message_suggests_prettier(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Fix error message suggests using Prettier.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with pytest.raises(NotImplementedError, match="Prettier"):
        markdownlint_plugin.fix([], {})
