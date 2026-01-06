"""Integration tests for Ruff flake8-bugbear (B) rule support."""

import pytest


@pytest.fixture(autouse=True)
def auto_skip_config_injection(skip_config_injection):
    """Disable Lintro config injection for all tests in this module.

    Uses the shared skip_config_injection fixture from conftest.py.

    Args:
        skip_config_injection: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield
