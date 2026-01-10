"""Shared fixtures for markdownlint plugin tests."""

from __future__ import annotations

import pytest

from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


@pytest.fixture
def markdownlint_plugin() -> MarkdownlintPlugin:
    """Provide a MarkdownlintPlugin instance for testing.

    Returns:
        A MarkdownlintPlugin instance.
    """
    return MarkdownlintPlugin()
