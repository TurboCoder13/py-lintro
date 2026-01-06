"""Integration tests for Mypy tool."""

import contextlib
import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from lintro.tools.implementations.tool_mypy import MypyTool


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode: object) -> Iterator[None]:
    """Disable config injection for predictable CLI args in tests.

    Args:
        lintro_test_mode: Pytest fixture that enables lintro test mode.

    Yields:
        None: Allows the test to run with modified environment.
    """
    yield


@contextlib.contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """Temporarily change the working directory.

    Args:
        path: Directory to make the temporary working directory.

    Yields:
        None: Restores the previous working directory after the context.
    """
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture
def mypy_tool() -> MypyTool:
    """Create a MypyTool instance for testing.

    Returns:
        MypyTool: Configured tool instance for assertions.
    """
    return MypyTool()


@pytest.fixture
def mypy_violation_file() -> Iterator[str]:
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
def mypy_clean_file() -> Iterator[str]:
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
