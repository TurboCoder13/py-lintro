"""Global test configuration for pytest.

Adds an optional gate for Docker tests to avoid spurious local failures.
Enable by setting environment variable `LINTRO_RUN_DOCKER_TESTS=1`.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from lintro.utils.path_utils import normalize_file_path_for_display

# Ensure stable docker builds under pytest-xdist by disabling BuildKit, which
# can be flaky with concurrent builds/tags on some local setups.
os.environ.setdefault("DOCKER_BUILDKIT", "0")


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_docker_images_built() -> None:
    """No-op placeholder to document Docker image provisioning.

    Images are now built by CI/scripts (e.g., scripts/docker/docker-test.sh)
    before tests run. Keeping a session autouse fixture maintains compatibility
    while avoiding any build work inside pytest processes.
    """
    return


def pytest_collection_modifyitems(config, items) -> None:
    """Optionally skip docker tests locally unless explicitly enabled.

    If `LINTRO_RUN_DOCKER_TESTS` is not set to "1", mark tests under
    `tests/scripts/docker/` to be skipped. CI can set the env var to run them.

    Args:
        config: Pytest configuration object.
        items: Collected test items that may be modified.
    """
    if os.getenv("LINTRO_RUN_DOCKER_TESTS") == "1":
        return

    skip_marker = pytest.mark.skip(
        reason="Docker tests disabled locally; set LINTRO_RUN_DOCKER_TESTS=1",
    )

    for item in items:
        # Path-based detection keeps it simple and non-invasive
        if "tests/scripts/docker/" in str(item.fspath):
            item.add_marker(skip_marker)


"""Shared fixtures used across tests in this repository."""


@pytest.fixture
def cli_runner():
    """Provide a Click CLI runner for testing.

    Returns:
        click.testing.CliRunner: CLI runner for invoking commands.
    """
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing.

    Yields:
        temp_dir (Path): Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def ruff_violation_file(temp_dir):
    """Copy the ruff_violations.py sample to a temp directory.

    return normalized path.

    Args:
        temp_dir (Path): Temporary directory fixture.

    Returns:
        str: Normalized path to the copied ruff_violations.py file.
    """
    src = Path("test_samples/ruff_violations.py").resolve()
    dst = temp_dir / "ruff_violations.py"
    shutil.copy(src, dst)
    return normalize_file_path_for_display(str(dst))


@pytest.fixture(autouse=True)
def clear_logging_handlers():
    """Clear logging handlers before each test.

    Yields:
        None: This fixture is used for its side effect only.
    """
    import logging

    logging.getLogger().handlers.clear()
    yield
