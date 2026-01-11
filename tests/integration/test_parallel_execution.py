"""Integration tests for parallel tool execution."""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator

import pytest
from assertpy import assert_that

from lintro.plugins import ToolRegistry
from lintro.utils.tool_executor import run_lint_tools_simple


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode: object) -> Iterator[None]:
    """Set test mode for all tests in this module.

    Args:
        lintro_test_mode: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield


@pytest.fixture
def temp_python_files() -> Iterator[list[str]]:
    """Create multiple temporary Python files for parallel testing.

    Yields:
        list[str]: List of paths to temporary Python files.
    """
    files: list[str] = []
    temp_dir = tempfile.mkdtemp()

    # Create multiple files with various issues
    file_contents = [
        (
            "file1.py",
            "import sys\nimport os\n\ndef add(a, b):\n    return a + b\n",
        ),
        (
            "file2.py",
            "def greet(name: str) -> str:\n    return f'Hello, {name}!'\n",
        ),
        (
            "file3.py",
            "import json\n\ndata = {'key': 'value'}\n",
        ),
    ]

    for filename, content in file_contents:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
        files.append(file_path)

    yield files

    # Cleanup
    for file_path in files:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)
    with contextlib.suppress(OSError):
        os.rmdir(temp_dir)


def test_check_multiple_files(temp_python_files: list[str]) -> None:
    """Test running check on multiple files.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    exit_code = run_lint_tools_simple(
        action="check",
        paths=temp_python_files,
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )

    # Should complete without crashing
    assert_that(exit_code).is_instance_of(int)


def test_consistent_results_across_runs(temp_python_files: list[str]) -> None:
    """Test that multiple runs produce consistent results.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    # Run twice
    exit_code_1 = run_lint_tools_simple(
        action="check",
        paths=temp_python_files,
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=False,
    )

    exit_code_2 = run_lint_tools_simple(
        action="check",
        paths=temp_python_files,
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=False,
    )

    # Exit codes should match
    assert_that(exit_code_1).is_equal_to(exit_code_2)


def test_check_with_single_file(temp_python_files: list[str]) -> None:
    """Test check with single file.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    exit_code = run_lint_tools_simple(
        action="check",
        paths=[temp_python_files[0]],
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=False,
    )

    assert_that(exit_code).is_instance_of(int)


def test_format_action(temp_python_files: list[str]) -> None:
    """Test format action.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    exit_code = run_lint_tools_simple(
        action="fmt",
        paths=temp_python_files,
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=False,
    )

    assert_that(exit_code).is_instance_of(int)


def test_different_output_formats(temp_python_files: list[str]) -> None:
    """Test different output formats.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    for fmt in ["grid", "plain", "json"]:
        exit_code = run_lint_tools_simple(
            action="check",
            paths=temp_python_files,
            tools="ruff",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format=fmt,
            verbose=False,
        )
        assert_that(exit_code).is_instance_of(int)


def test_tool_definition_exists() -> None:
    """Test that ruff tool has proper definition."""
    ruff_tool = ToolRegistry.get("ruff")

    assert_that(ruff_tool).is_not_none()
    assert_that(ruff_tool.definition).is_not_none()
    assert_that(ruff_tool.definition.name).is_equal_to("ruff")


def test_tool_respects_execution_order(temp_python_files: list[str]) -> None:
    """Test that tool execution order is predictable.

    Args:
        temp_python_files: Pytest fixture providing temp files.
    """
    # Run multiple times to verify consistency
    results = []
    for _ in range(3):
        exit_code = run_lint_tools_simple(
            action="check",
            paths=temp_python_files,
            tools="ruff",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="grid",
            verbose=False,
        )
        results.append(exit_code)

    # All runs should produce same exit code
    assert_that(len(set(results))).is_equal_to(1)
