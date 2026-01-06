"""Integration tests for Ruff tool."""

import contextlib
import os
import shutil
import tempfile

import pytest
from loguru import logger

from lintro.tools.implementations.tool_ruff import RuffTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode):
    """Set LINTRO_TEST_MODE=1 and disable config injection for all tests.

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

    Returns:
        RuffTool: A configured RuffTool instance.
    """
    return RuffTool()


@pytest.fixture
def ruff_violation_file():
    """Copy the ruff_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary ruff_violations.py file.
    """
    src = os.path.abspath("test_samples/tools/python/ruff/ruff_e501_f401_violations.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "ruff_violations.py")
        shutil.copy(src, dst)
        yield dst


@pytest.fixture
def ruff_clean_file():
    """Return the path to the static Ruff-clean file for testing.

    Yields:
        str: Path to the static ruff_clean.py file.
    """
    yield os.path.abspath("test_samples/tools/python/ruff/ruff_clean.py")


@pytest.fixture
def temp_python_file(request):
    """Create a temporary Python file with ruff violations.

    Args:
        request: Pytest request fixture for finalizer registration.

    Yields:
        str: Path to the temporary Python file with violations.
    """
    content = (
        "# Test file with ruff violations\n\n"
        "import sys,os\n"
        "import json\n"
        "from pathlib    import Path\n\n"
        "def hello(name:str='World'):\n"
        "    print(f'Hello, {name}!')\n"
        "    unused_var = 42\n\n"
        "if __name__=='__main__':\n"
        "    hello()\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = f.name
    print(f"[DEBUG] temp_python_file path: {file_path}")
    with open(file_path) as debug_f:
        print("[DEBUG] temp_python_file contents:")
        print(debug_f.read())

    def cleanup() -> None:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)

    request.addfinalizer(cleanup)
    yield file_path
