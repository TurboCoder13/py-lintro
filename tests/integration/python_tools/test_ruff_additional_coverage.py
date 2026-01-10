"""Additional test coverage for Ruff tool changes."""

import os
import tempfile

import pytest

from lintro.plugins import ToolRegistry


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode):
    """Set LINTRO_TEST_MODE=1 and skip config injection for all tests.

    Uses the shared lintro_test_mode fixture from conftest.py.

    Args:
        lintro_test_mode: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield


@pytest.fixture
def ruff_tool():
    """Create a RuffTool instance for testing.

    Config injection is already disabled by set_lintro_test_mode_env fixture.

    Yields:
        RuffTool: A configured RuffTool instance.
    """
    yield ToolRegistry.get("ruff")


@pytest.fixture
def ruff_clean_file():
    """Return the path to the static Ruff-clean file for testing.

    Yields:
        str: Path to the static ruff_clean.py file.
    """
    yield os.path.abspath("test_samples/tools/python/ruff/ruff_clean.py")


@pytest.fixture
def ruff_violation_file():
    """Copy the ruff_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary ruff_violations.py file.
    """
    import shutil

    src = os.path.abspath("test_samples/tools/python/ruff/ruff_e501_f401_violations.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "ruff_violations.py")
        shutil.copy(src, dst)
        yield dst
