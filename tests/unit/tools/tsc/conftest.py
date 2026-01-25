"""Fixtures for tsc tool tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from lintro.tools.definitions.tsc import TscPlugin


@pytest.fixture
def tsc_plugin() -> TscPlugin:
    """Provide a TscPlugin instance for testing.

    Returns:
        A TscPlugin instance.
    """
    from lintro.tools.definitions.tsc import TscPlugin

    return TscPlugin()


@pytest.fixture
def tsc_plugin_with_mocked_tsc() -> Generator[TscPlugin, None, None]:
    """Provide a TscPlugin with tsc availability mocked.

    Yields:
        A TscPlugin instance with shutil.which mocked.
    """
    from lintro.tools.definitions.tsc import TscPlugin

    with patch("shutil.which") as mock_which:
        mock_which.side_effect = lambda x: "/usr/bin/tsc" if x == "tsc" else None
        yield TscPlugin()
