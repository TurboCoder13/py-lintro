"""Pytest configuration for tsc tests."""

from __future__ import annotations

import pytest

from lintro.tools.definitions.tsc import TscPlugin


@pytest.fixture
def tsc_plugin() -> TscPlugin:
    """Provide a TscPlugin instance for testing.

    Returns:
        A TscPlugin instance.
    """
    return TscPlugin()
