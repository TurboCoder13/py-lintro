"""Integration tests for Ruff tool."""

import contextlib
import os
import shutil
import tempfile

import pytest
from assertpy import assert_that
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

    def test_sim_simplify_fixing(self, ruff_tool) -> None:
        """Test SIM (flake8-simplify) rule fixing.

        Args:
            self: Test instance.
            ruff_tool: RuffTool fixture instance.
        """
        import os
        import tempfile

        # Create a temporary file with SIM violations
        content = """
def test_function():
    x = 5
    # SIM101: Unnecessary if-else
    if x > 0:
        result = True
    else:
        result = False
    return result
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_file = f.name

        try:
            # Check initial issues
            ruff_tool.set_options(select=["SIM"], unsafe_fixes=True)
            initial_result = ruff_tool.check([temp_file])
            initial_count = initial_result.issues_count

            # Apply fixes
            fix_result = ruff_tool.fix([temp_file])
            assert_that(fix_result.success).is_true()

            # Check remaining issues
            final_result = ruff_tool.check([temp_file])
            final_count = final_result.issues_count

            # Should have fewer issues after fixing
            assert_that(final_count).is_less_than_or_equal_to(initial_count)

        finally:
            os.unlink(temp_file)
