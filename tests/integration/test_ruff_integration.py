"""Integration tests for Ruff tool."""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.plugins import ToolRegistry

if TYPE_CHECKING:
    from lintro.plugins.base import BaseToolPlugin


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode: object) -> Iterator[None]:
    """Set LINTRO_TEST_MODE=1 and disable config injection for all tests.

    Uses the shared lintro_test_mode fixture from conftest.py.

    Args:
        lintro_test_mode: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield


@pytest.fixture
def ruff_tool() -> BaseToolPlugin:
    """Create a fresh RuffPlugin instance for testing.

    Creates a new instance to avoid test pollution from shared state.

    Returns:
        BaseToolPlugin: A fresh RuffPlugin instance.
    """
    # Create a fresh instance to avoid test pollution
    ToolRegistry._ensure_discovered()
    plugin_class = ToolRegistry._tools["ruff"]
    return plugin_class()


@pytest.fixture
def ruff_clean_file() -> Iterator[str]:
    """Return the path to the static Ruff-clean file for testing.

    Yields:
        str: Path to the static ruff_clean.py file.
    """
    yield os.path.abspath("test_samples/tools/python/ruff/ruff_clean.py")


@pytest.fixture
def temp_python_file(request: pytest.FixtureRequest) -> Iterator[str]:
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

    def cleanup() -> None:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)

    request.addfinalizer(cleanup)
    yield file_path


def test_ruff_tool_available(ruff_tool: BaseToolPlugin) -> None:
    """Test that ruff tool is registered and available.

    Args:
        ruff_tool: Pytest fixture providing the ruff tool instance.
    """
    assert_that(ruff_tool).is_not_none()
    assert_that(ruff_tool.definition.name).is_equal_to("ruff")


def test_ruff_check_finds_violations(
    ruff_tool: BaseToolPlugin,
    temp_python_file: str,
) -> None:
    """Test that ruff check finds violations in file with issues.

    Args:
        ruff_tool: Pytest fixture providing the ruff tool instance.
        temp_python_file: Pytest fixture providing temp file with violations.
    """
    result = ruff_tool.check([temp_python_file], {})

    assert_that(result).is_not_none()
    assert_that(result.success).is_false()
    assert_that(result.issues).is_not_none()
    assert_that(result.issues).is_not_empty()
    # Check that we found expected violations (F401 unused import, etc.)
    # Note: Some issues are RuffFormatIssue which don't have code attribute
    issues = result.issues or []
    issue_codes = [issue.code for issue in issues if hasattr(issue, "code")]
    assert_that(any("F401" in str(code) for code in issue_codes)).is_true()


def test_ruff_check_clean_file(
    ruff_tool: BaseToolPlugin,
    ruff_clean_file: str,
) -> None:
    """Test that ruff check passes on clean file.

    Args:
        ruff_tool: Pytest fixture providing the ruff tool instance.
        ruff_clean_file: Pytest fixture providing path to clean file.
    """
    if not os.path.exists(ruff_clean_file):
        pytest.skip(f"Clean sample file {ruff_clean_file} does not exist")

    result = ruff_tool.check([ruff_clean_file], {})

    assert_that(result).is_not_none()
    assert_that(result.success).is_true()
    # issues can be None or an empty list when no issues found
    assert_that(result.issues is None or len(result.issues) == 0).is_true()


def test_ruff_fix_modifies_file(
    ruff_tool: BaseToolPlugin,
    temp_python_file: str,
) -> None:
    """Test that ruff fix modifies file with formatting issues.

    Args:
        ruff_tool: Pytest fixture providing the ruff tool instance.
        temp_python_file: Pytest fixture providing temp file with violations.
    """
    with open(temp_python_file) as f:
        original_content = f.read()

    result = ruff_tool.fix([temp_python_file], {})

    assert_that(result).is_not_none()

    with open(temp_python_file) as f:
        modified_content = f.read()

    # Content should be different (formatted/fixed)
    assert_that(modified_content).is_not_equal_to(original_content)


def test_ruff_handles_empty_path_list(ruff_tool: BaseToolPlugin) -> None:
    """Test that ruff handles empty path list gracefully.

    Args:
        ruff_tool: Pytest fixture providing the ruff tool instance.
    """
    result = ruff_tool.check([], {})

    # Should complete without crashing
    assert_that(result).is_not_none()
