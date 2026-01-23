"""Pytest configuration for oxfmt tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.oxfmt import OxfmtPlugin


@pytest.fixture
def oxfmt_plugin() -> OxfmtPlugin:
    """Provide an OxfmtPlugin instance for testing.

    Returns:
        An OxfmtPlugin instance.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return OxfmtPlugin()
