"""Shared fixtures for config unit tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a temporary directory with config files.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to temporary config directory.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create sample pyproject.toml
    pyproject_content = """
[tool.lintro]
line_length = 88

[tool.ruff]
line-length = 88

[tool.black]
line_length = 88
"""
    (config_dir / "pyproject.toml").write_text(pyproject_content)

    return config_dir


@pytest.fixture
def mock_config_loader():
    """Provide a mock config loader for testing.

    Returns:
        MagicMock: Mock config loader instance.
    """
    loader = MagicMock()
    loader.load_config.return_value = {
        "line_length": 88,
        "tool_order": "priority",
    }
    return loader
