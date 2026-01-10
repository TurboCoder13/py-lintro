"""Shared fixtures for yamllint plugin tests."""

from __future__ import annotations

import pytest

from lintro.tools.definitions.yamllint import YamllintPlugin


@pytest.fixture
def yamllint_plugin() -> YamllintPlugin:
    """Provide a YamllintPlugin instance for testing.

    Returns:
        YamllintPlugin: A fresh YamllintPlugin instance.
    """
    return YamllintPlugin()
