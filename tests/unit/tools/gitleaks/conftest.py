"""Pytest configuration for gitleaks tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.gitleaks import GitleaksPlugin


@pytest.fixture
def gitleaks_plugin() -> GitleaksPlugin:
    """Provide a GitleaksPlugin instance for testing.

    Returns:
        A GitleaksPlugin instance.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return GitleaksPlugin()
