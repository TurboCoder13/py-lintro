"""Pytest configuration for UnifiedConfigManager unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from lintro.utils.unified_config import UnifiedConfigManager

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_manager_dependencies() -> Generator[None, None, None]:
    """Mock all dependencies needed to create a UnifiedConfigManager.

    This fixture patches all config loading functions to return empty defaults,
    allowing UnifiedConfigManager to be instantiated without filesystem access.

    Yields:
        Context manager for mocking config dependencies.
    """
    with (
        patch(
            "lintro.utils.unified_config_manager.load_lintro_global_config",
            return_value={},
        ),
        patch(
            "lintro.utils.unified_config_manager.get_tool_config_summary",
            return_value={},
        ),
        patch(
            "lintro.utils.unified_config_manager.validate_config_consistency",
            return_value=[],
        ),
    ):
        yield


@pytest.fixture
def manager(mock_manager_dependencies: None) -> UnifiedConfigManager:
    """Create a UnifiedConfigManager instance with mocked dependencies.

    Args:
        mock_manager_dependencies: Mocked dependencies fixture.

    Returns:
        An initialized UnifiedConfigManager for testing.
    """
    return UnifiedConfigManager()


@pytest.fixture
def mock_tool() -> MagicMock:
    """Create a mock tool object with name and set_options method.

    Returns:
        MagicMock configured to act like a tool instance.
    """
    mock = MagicMock()
    mock.name = "ruff"
    return mock
