"""Shared fixtures for pydoclint plugin tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.pydoclint import PydoclintPlugin


@pytest.fixture
def pydoclint_plugin() -> PydoclintPlugin:
    """Provide a PydoclintPlugin instance for testing.

    Returns:
        A PydoclintPlugin instance.
    """
    with patch(
        "lintro.tools.definitions.pydoclint.load_pydoclint_config",
        return_value={},
    ):
        return PydoclintPlugin()
