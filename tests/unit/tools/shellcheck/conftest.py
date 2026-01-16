"""Pytest configuration for shellcheck tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lintro.tools.definitions.shellcheck import ShellcheckPlugin


@pytest.fixture
def shellcheck_plugin() -> ShellcheckPlugin:
    """Provide a ShellcheckPlugin instance for testing.

    Returns:
        A ShellcheckPlugin instance.
    """
    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        return ShellcheckPlugin()
