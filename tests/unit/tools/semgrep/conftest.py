"""Pytest configuration for semgrep tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.semgrep import SemgrepPlugin


@pytest.fixture
def semgrep_plugin() -> SemgrepPlugin:
    """Provide a SemgrepPlugin instance for testing.

    Returns:
        A SemgrepPlugin instance.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return SemgrepPlugin()
