"""Shared fixtures for biome plugin tests."""

from __future__ import annotations

import pytest

from lintro.tools.definitions.biome import BiomePlugin


@pytest.fixture
def biome_plugin() -> BiomePlugin:
    """Provide a BiomePlugin instance for testing.

    Returns:
        BiomePlugin: A new BiomePlugin instance.
    """
    return BiomePlugin()
