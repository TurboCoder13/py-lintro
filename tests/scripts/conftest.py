"""Shared fixtures for CI script tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_script_dir():
    """Create a temporary directory with script testing setup.

    Yields:
        Path: Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        script_dir = Path(tmpdir)
        # Copy necessary files for script testing
        yield script_dir


@pytest.fixture
def mock_github_env():
    """Mock GitHub Actions environment variables.

    Yields:
        dict: Dictionary of mocked environment variables.
    """
    env_vars = {
        "GITHUB_TOKEN": "mock-token",
        "GITHUB_REPOSITORY": "test/repo",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REF": "refs/pull/123/merge",
        "GITHUB_SHA": "abc123def456",
    }

    original_env = {}
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield env_vars
    finally:
        for key, original_value in original_env.items():
            if original_value is not None:
                os.environ[key] = original_value
            else:
                os.environ.pop(key, None)
