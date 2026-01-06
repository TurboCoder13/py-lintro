"""Shared fixtures for integration tests."""

import os
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path]:
    """Create a temporary directory structure for integration testing.

    Yields:
        Path: Path to the temporary project directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        # Create a basic project structure
        (project_dir / "pyproject.toml").write_text(
            """[tool.lintro]
line_length = 88

[tool.ruff]
line-length = 88
""",
        )
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()

        # Change to the temp directory for the test
        original_cwd = os.getcwd()
        os.chdir(project_dir)
        try:
            yield project_dir
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def lintro_test_mode() -> Generator[str]:
    """Set LINTRO_TEST_MODE=1 environment variable for tests.

    This disables config injection and other test-incompatible features.

    Yields:
        str: The test mode value that was set.
    """
    original_value = os.environ.get("LINTRO_TEST_MODE")
    os.environ["LINTRO_TEST_MODE"] = "1"
    try:
        yield "1"
    finally:
        if original_value is not None:
            os.environ["LINTRO_TEST_MODE"] = original_value
        else:
            os.environ.pop("LINTRO_TEST_MODE", None)


@pytest.fixture
def skip_if_tool_unavailable() -> Callable[[str], None]:
    """Skip test if required tool is not available in PATH.

    Returns:
        callable: Function that takes a tool_name (str) parameter and can be used
        to skip tests for unavailable tools.
    """

    def _skip_if_unavailable(tool_name: str) -> None:
        """Skip the current test if tool is not available.

        Args:
            tool_name: Name of the tool to check for availability.
        """
        import shutil

        if not shutil.which(tool_name):
            pytest.skip(f"Tool '{tool_name}' not available in PATH")

    return _skip_if_unavailable
