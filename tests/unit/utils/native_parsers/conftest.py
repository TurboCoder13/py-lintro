"""Shared fixtures for native_parsers tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_empty_pyproject() -> Iterator[MagicMock]:
    """Fixture that mocks load_pyproject to return an empty dict.

    Yields:
        Mock object for load_pyproject function.
    """
    with patch("lintro.utils.config.load_pyproject") as mock_load:
        mock_load.return_value = {}
        yield mock_load


@pytest.fixture
def temp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture that changes the current working directory to a temp path.

    Args:
        tmp_path: Temporary directory path.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The temporary directory path.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
