"""Integration tests for Mypy tool definition.

These tests require mypy to be installed and available in PATH.
They verify the MypyPlugin definition, check command, and set_options method.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.plugins.base import BaseToolPlugin

# Skip all tests if mypy is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("mypy") is None,
    reason="mypy not installed",
)


@pytest.fixture
def temp_python_file_with_type_errors(tmp_path: Path) -> str:
    """Create a temporary Python file with type errors.

    Creates a file containing code with deliberate type annotation violations
    that mypy should detect, including:
    - Passing string arguments where int is expected
    - Assigning int to a str-typed variable

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "type_errors.py"
    file_path.write_text(
        """\
def add(a: int, b: int) -> int:
    return a + b

# Type error: passing string instead of int
result: int = add("hello", "world")

def greet(name: str) -> str:
    return "Hello, " + name

# Type error: assigning int to str variable
greeting: str = 42
""",
    )
    return str(file_path)


@pytest.fixture
def temp_python_file_type_correct(tmp_path: Path) -> str:
    """Create a temporary Python file with correct types.

    Creates a file containing properly typed Python code that should
    pass mypy type checking without errors.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "type_correct.py"
    file_path.write_text(
        """\
def add(a: int, b: int) -> int:
    return a + b


result: int = add(1, 2)


def greet(name: str) -> str:
    return "Hello, " + name


greeting: str = greet("World")
""",
    )
    return str(file_path)


# --- Tests for MypyPlugin definition ---


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("name", "mypy"),
        ("can_fix", False),
    ],
    ids=["name", "can_fix"],
)
def test_definition_attributes(
    get_plugin: Callable[[str], BaseToolPlugin],
    attr: str,
    expected: object,
) -> None:
    """Verify MypyPlugin definition has correct attribute values.

    Tests that the plugin definition exposes the expected values for
    name and can_fix attributes.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        attr: The attribute name to check on the definition.
        expected: The expected value of the attribute.
    """
    mypy_plugin = get_plugin("mypy")
    assert_that(getattr(mypy_plugin.definition, attr)).is_equal_to(expected)


def test_definition_file_patterns(get_plugin: Callable[[str], BaseToolPlugin]) -> None:
    """Verify MypyPlugin definition includes Python file patterns.

    Tests that the plugin is configured to handle Python files (*.py).

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    mypy_plugin = get_plugin("mypy")
    assert_that(mypy_plugin.definition.file_patterns).contains("*.py")


# --- Integration tests for mypy check command ---


def test_check_file_with_type_errors(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_python_file_with_type_errors: str,
) -> None:
    """Verify mypy check detects type errors in problematic files.

    Runs mypy on a file containing deliberate type violations and verifies
    that issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_python_file_with_type_errors: Path to file with type errors.
    """
    mypy_plugin = get_plugin("mypy")
    result = mypy_plugin.check([temp_python_file_with_type_errors], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("mypy")
    assert_that(result.issues_count).is_greater_than(0)


def test_check_type_correct_file(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_python_file_type_correct: str,
) -> None:
    """Verify mypy check passes on type-correct files.

    Runs mypy on a properly typed file and verifies no issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_python_file_type_correct: Path to file with correct types.
    """
    mypy_plugin = get_plugin("mypy")
    result = mypy_plugin.check([temp_python_file_type_correct], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("mypy")
    assert_that(result.issues_count).is_equal_to(0)


def test_check_empty_directory(
    get_plugin: Callable[[str], BaseToolPlugin],
    tmp_path: Path,
) -> None:
    """Verify mypy check handles empty directories gracefully.

    Runs mypy on an empty directory and verifies a result is returned
    without errors.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tmp_path: Pytest fixture providing a temporary directory.
    """
    mypy_plugin = get_plugin("mypy")
    result = mypy_plugin.check([str(tmp_path)], {})

    assert_that(result).is_not_none()


# --- Tests for MypyPlugin.set_options method ---


@pytest.mark.parametrize(
    ("option_name", "option_value", "expected"),
    [
        ("strict", True, True),
        ("ignore_missing_imports", True, True),
    ],
    ids=["strict", "ignore_missing_imports"],
)
def test_set_options(
    get_plugin: Callable[[str], BaseToolPlugin],
    option_name: str,
    option_value: object,
    expected: object,
) -> None:
    """Verify MypyPlugin.set_options correctly sets various options.

    Tests that plugin options can be set and retrieved correctly.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
        expected: Expected value when retrieving the option.
    """
    mypy_plugin = get_plugin("mypy")
    mypy_plugin.set_options(**{option_name: option_value})
    assert_that(mypy_plugin.options.get(option_name)).is_equal_to(expected)
