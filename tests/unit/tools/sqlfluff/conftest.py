"""Pytest configuration for sqlfluff tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.sqlfluff import SqlfluffPlugin


@pytest.fixture
def sqlfluff_plugin() -> SqlfluffPlugin:
    """Provide a SqlfluffPlugin instance for testing.

    Returns:
        A SqlfluffPlugin instance.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return SqlfluffPlugin()
