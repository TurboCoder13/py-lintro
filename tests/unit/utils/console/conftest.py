"""Shared fixtures for console logger tests.

Provides common imports and fixtures used across logger test modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from lintro.utils.console.logger import ThreadSafeConsoleLogger

if TYPE_CHECKING:
    pass


@pytest.fixture
def logger() -> ThreadSafeConsoleLogger:
    """Provide a default ThreadSafeConsoleLogger instance.

    Returns:
        A ThreadSafeConsoleLogger with no run directory configured.
    """
    return ThreadSafeConsoleLogger()


@pytest.fixture
def logger_with_run_dir(tmp_path: Path) -> ThreadSafeConsoleLogger:
    """Provide a ThreadSafeConsoleLogger with a run directory configured.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        A ThreadSafeConsoleLogger configured with a run directory.
    """
    return ThreadSafeConsoleLogger(run_dir=tmp_path)
