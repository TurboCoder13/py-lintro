"""Pytest configuration for taplo tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.taplo import TaploPlugin


@pytest.fixture
def taplo_plugin() -> TaploPlugin:
    """Provide a TaploPlugin instance for testing.

    Returns:
        A TaploPlugin instance.
    """
    with patch(
        "lintro.plugins.base.verify_tool_version",
        return_value=None,
    ):
        return TaploPlugin()
