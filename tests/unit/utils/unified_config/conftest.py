"""Shared fixtures for unified_config tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_empty_tool_order_config() -> Any:
    """Mock get_tool_order_config to return empty dict.

    Yields:
        Context manager for mocking tool order config.
    """
    with patch(
        "lintro.utils.config_priority.get_tool_order_config",
        return_value={},
    ):
        yield


@pytest.fixture
def mock_empty_configs() -> Any:
    """Mock all config loaders to return empty dicts.

    Yields:
        Context manager for mocking all config loaders.
    """
    with (
        patch(
            "lintro.utils.config_priority.load_lintro_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_priority.load_lintro_global_config",
            return_value={},
        ),
        patch("lintro.utils.config_priority.load_pyproject", return_value={}),
        patch(
            "lintro.utils.config_priority._load_native_tool_config",
            return_value={},
        ),
    ):
        yield
