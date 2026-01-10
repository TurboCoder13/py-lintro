"""Shared fixtures for black plugin tests."""

from __future__ import annotations

import pytest

from lintro.tools.definitions.black import BlackPlugin


@pytest.fixture
def black_plugin() -> BlackPlugin:
    """Provide a BlackPlugin instance for testing.

    Returns:
        BlackPlugin: A new BlackPlugin instance.
    """
    return BlackPlugin()
