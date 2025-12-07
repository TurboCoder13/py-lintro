"""Integration tests for Mypy tool."""

import contextlib
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_mypy import MypyTool


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode):
    """Disable config injection for predictable CLI args in tests.

    Args:
        lintro_test_mode: Pytest fixture that enables lintro test mode.

    Yields:
        None: Allows the test to run with modified environment.
    """
    yield


@pytest.fixture
def mypy_tool():
    """Create a MypyTool instance for testing.

    Returns:
        MypyTool: Configured tool instance for assertions.
    """
    return MypyTool()


@pytest.fixture
def mypy_violation_file():
    """Copy the mypy_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary file containing known mypy violations.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    src = repo_root / "test_samples" / "mypy_violations.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "mypy_violations.py")
        shutil.copy(src, dst)
        yield dst


@pytest.fixture
def mypy_clean_file():
    """Create a temporary clean Python file for mypy.

    Yields:
        str: Path to a temporary Python file without mypy violations.
    """
    content = (
        "from typing import Annotated\n\n"
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        file_path = f.name
    try:
        yield file_path
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)


class TestMypyTool:
    """Test cases for MypyTool."""

    def test_tool_initialization_defaults(self, mypy_tool) -> None:
        """Ensure defaults align with pyproject and ignore missing imports.

        Args:
            mypy_tool: Tool instance under test.
        """
        assert_that(mypy_tool.name).is_equal_to("mypy")
        assert_that(mypy_tool.options["strict"]).is_false()
        assert_that(mypy_tool.options["ignore_missing_imports"]).is_true()

    def test_lint_check_clean_file(self, mypy_tool, mypy_clean_file) -> None:
        """Check a typed file should pass without issues.

        Args:
            mypy_tool: Tool instance under test.
            mypy_clean_file: Path to a clean file.
        """
        result = mypy_tool.check([mypy_clean_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)

    def test_lint_check_violations(self, mypy_tool, mypy_violation_file) -> None:
        """Check a file with mypy violations should fail.

        Args:
            mypy_tool: Tool instance under test.
            mypy_violation_file: Path to a file with deliberate mypy errors.
        """
        result = mypy_tool.check([mypy_violation_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_greater_than(0)
