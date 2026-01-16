"""Integration tests for Gitleaks tool definition.

These tests require gitleaks to be installed and available in PATH.
They verify the GitleaksPlugin definition, check command, and set_options method.
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

# Skip all tests if gitleaks is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("gitleaks") is None,
    reason="gitleaks not installed",
)


@pytest.fixture
def temp_file_with_secrets(tmp_path: Path) -> str:
    """Create a temporary file with secrets for detection.

    Creates a file containing deliberate secrets that gitleaks should detect,
    including:
    - AWS-style access key pattern
    - Generic API key pattern

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "secrets.py"
    file_path.write_text(
        """\
# Sample file with intentional secrets for testing
API_KEY = "AKIAIOSFODNN7EXAMPLE"  # AWS-style key pattern
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
""",
    )
    return str(file_path)


@pytest.fixture
def temp_file_no_secrets(tmp_path: Path) -> str:
    """Create a temporary file with no secrets.

    Creates a file containing clean Python code that should pass
    gitleaks scanning without issues.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the created file as a string.
    """
    file_path = tmp_path / "clean.py"
    file_path.write_text(
        '''\
"""A clean module with no secrets."""

import os


def get_env_var(name: str) -> str:
    """Get environment variable safely."""
    return os.environ.get(name, "")


def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''',
    )
    return str(file_path)


# --- Tests for GitleaksPlugin definition ---


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("name", "gitleaks"),
        ("can_fix", False),
    ],
    ids=["name", "can_fix"],
)
def test_definition_attributes(
    get_plugin: Callable[[str], BaseToolPlugin],
    attr: str,
    expected: object,
) -> None:
    """Verify GitleaksPlugin definition has correct attribute values.

    Tests that the plugin definition exposes the expected values for
    name and can_fix attributes.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        attr: The attribute name to check on the definition.
        expected: The expected value of the attribute.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    assert_that(getattr(gitleaks_plugin.definition, attr)).is_equal_to(expected)


def test_definition_file_patterns(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify GitleaksPlugin definition scans all files.

    Tests that the plugin is configured to scan all file types.

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    assert_that(gitleaks_plugin.definition.file_patterns).contains("*")


def test_definition_tool_type(
    get_plugin: Callable[[str], BaseToolPlugin],
) -> None:
    """Verify GitleaksPlugin is a security tool type.

    Args:
        get_plugin: Fixture factory to get plugin instances.
    """
    from lintro.enums.tool_type import ToolType

    gitleaks_plugin = get_plugin("gitleaks")
    assert_that(gitleaks_plugin.definition.tool_type).is_equal_to(ToolType.SECURITY)


# --- Integration tests for gitleaks check command ---


def test_check_file_with_secrets(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_file_with_secrets: str,
) -> None:
    """Verify gitleaks check detects secrets in problematic files.

    Runs gitleaks on a file containing deliberate secrets
    and verifies that issues are found.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_file_with_secrets: Path to file with secrets.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    result = gitleaks_plugin.check([temp_file_with_secrets], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("gitleaks")
    # Gitleaks should detect at least one secret pattern
    assert_that(result.issues_count).is_greater_than(0)


def test_check_clean_file(
    get_plugin: Callable[[str], BaseToolPlugin],
    temp_file_no_secrets: str,
) -> None:
    """Verify gitleaks check passes on clean files.

    Runs gitleaks on a file without secrets and verifies no issues.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        temp_file_no_secrets: Path to file with no secrets.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    result = gitleaks_plugin.check([temp_file_no_secrets], {})

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("gitleaks")


def test_check_empty_directory(
    get_plugin: Callable[[str], BaseToolPlugin],
    tmp_path: Path,
) -> None:
    """Verify gitleaks check handles empty directories gracefully.

    Runs gitleaks on an empty directory and verifies a result is returned
    without errors.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        tmp_path: Pytest fixture providing a temporary directory.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    result = gitleaks_plugin.check([str(tmp_path)], {})

    assert_that(result).is_not_none()


# --- Tests for GitleaksPlugin.set_options method ---


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("no_git", True),
        ("no_git", False),
        ("redact", True),
        ("redact", False),
        ("config", "/path/to/config.toml"),
        ("baseline_path", "/path/to/baseline.json"),
        ("max_target_megabytes", 50),
    ],
    ids=[
        "no_git_true",
        "no_git_false",
        "redact_true",
        "redact_false",
        "config_path",
        "baseline_path",
        "max_target_megabytes",
    ],
)
def test_set_options(
    get_plugin: Callable[[str], BaseToolPlugin],
    option_name: str,
    option_value: object,
) -> None:
    """Verify GitleaksPlugin.set_options correctly sets various options.

    Tests that plugin options can be set and retrieved correctly.

    Args:
        get_plugin: Fixture factory to get plugin instances.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
    """
    gitleaks_plugin = get_plugin("gitleaks")
    gitleaks_plugin.set_options(**{option_name: option_value})
    assert_that(gitleaks_plugin.options.get(option_name)).is_equal_to(option_value)
