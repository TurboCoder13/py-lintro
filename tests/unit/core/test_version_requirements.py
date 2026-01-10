"""Tests for version requirements functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that
from packaging.version import Version

if TYPE_CHECKING:
    pass

from lintro.tools.core.version_parsing import (
    ToolVersionInfo,
    check_tool_version,
    compare_versions,
    extract_version_from_output,
    get_install_hints,
    get_minimum_versions,
    parse_version,
)
from lintro.tools.core.version_requirements import get_all_tool_versions


@pytest.mark.parametrize(
    "version_str,expected",
    [
        ("1.2.3", Version("1.2.3")),
        ("0.14.0", Version("0.14.0")),
        ("2.0", Version("2.0")),
        ("1.0.0-alpha", Version("1.0.0")),  # Pre-release suffix stripped
        ("v1.5.0", Version("1.5.0")),  # Handle leading 'v'
    ],
)
def test_parse_version(version_str: str, expected: Version) -> None:
    """Test version string parsing using packaging.version.

    Args:
        version_str: Version string to parse.
        expected: Expected parsed Version object.
    """
    assert_that(parse_version(version_str)).is_equal_to(expected)


def test_parse_version_invalid() -> None:
    """Test that parse_version raises ValueError for invalid input."""
    with pytest.raises(ValueError, match="Unable to parse version string"):
        parse_version("invalid")


@pytest.mark.parametrize(
    "version1,version2,expected",
    [
        ("1.2.3", "1.2.3", 0),  # Equal
        ("1.2.3", "1.2.4", -1),  # version1 < version2
        ("1.3.0", "1.2.4", 1),  # version1 > version2
        ("2.0.0", "1.9.9", 1),  # Major version difference
        ("1.10.0", "1.2.0", 1),  # Minor version difference
    ],
)
def test_compare_versions(version1: str, version2: str, expected: int) -> None:
    """Test version comparison.

    Args:
        version1: First version string to compare.
        version2: Second version string to compare.
        expected: Expected comparison result (-1, 0, or 1).
    """
    assert_that(compare_versions(version1, version2)).is_equal_to(expected)


@pytest.mark.parametrize(
    "tool_name,output,expected",
    [
        ("black", "black, 25.9.0 (compiled: yes)", "25.9.0"),
        ("bandit", "__main__.py 1.8.6", "1.8.6"),
        ("hadolint", "Haskell Dockerfile Linter 2.14.0", "2.14.0"),
        ("prettier", "Prettier 3.7.3", "3.7.3"),
        ("actionlint", "actionlint 1.7.5", "1.7.5"),
        ("biome", "Biome CLI v2.3.8", "2.3.8"),
        ("darglint", "1.8.1", "1.8.1"),
        ("ruff", "ruff 0.14.4", "0.14.4"),
        ("yamllint", "yamllint 1.37.1", "1.37.1"),
        # Clippy: rustc output should extract Rust version directly
        ("clippy", "rustc 1.92.0 (ded5c06cf 2025-12-08)", "1.92.0"),
        # Clippy: clippy output should convert 0.1.X to 1.X.0
        ("clippy", "clippy 0.1.92 (ded5c06cf2 2025-12-08)", "1.92.0"),
        ("clippy", "clippy 0.1.75 (abcdef123 2024-01-01)", "1.75.0"),
    ],
)
def test_extract_version_from_output(
    tool_name: str,
    output: str,
    expected: str,
) -> None:
    """Test version extraction from various tool outputs.

    Args:
        tool_name: Name of the tool.
        output: Raw version output string from tool.
        expected: Expected extracted version string.
    """
    assert_that(extract_version_from_output(output, tool_name)).is_equal_to(expected)


def test_get_minimum_versions_from_pyproject() -> None:
    """Test reading minimum versions from pyproject.toml."""
    versions = get_minimum_versions()

    # Should include bundled tools from dependencies
    assert_that(versions).contains_key("ruff")
    assert_that(versions).contains_key("black")
    assert_that(versions).contains_key("bandit")
    assert_that(versions).contains_key("yamllint")
    assert_that(versions).contains_key("darglint")

    # Should include tools from [tool.lintro.versions]
    assert_that(versions).contains_key("prettier")
    assert_that(versions).contains_key("hadolint")
    assert_that(versions).contains_key("actionlint")
    assert_that(versions).contains_key("pytest")

    # Versions should be strings
    assert_that(versions["ruff"]).is_instance_of(str)
    assert_that(versions["prettier"]).is_instance_of(str)


def test_get_install_hints() -> None:
    """Test generating install hints."""
    hints = get_install_hints()

    assert_that(hints).contains_key("ruff")
    assert_that(hints).contains_key("prettier")
    assert_that(hints["ruff"]).contains("Install via:")
    assert_that(hints["prettier"]).contains("npm install")


def test_version_caching() -> None:
    """Test that versions are cached properly."""
    # First call
    versions1 = get_minimum_versions()
    hints1 = get_install_hints()

    # Second call should return equal values (cached)
    versions2 = get_minimum_versions()
    hints2 = get_install_hints()

    assert_that(versions1).is_equal_to(versions2)
    assert_that(hints1).is_equal_to(hints2)


@patch("subprocess.run")
def test_check_tool_version_success(mock_run: MagicMock) -> None:
    """Test successful version check.

    Args:
        mock_run: Mocked subprocess.run function.
    """
    mock_run.return_value = type(
        "MockResult",
        (),
        {
            "returncode": 0,
            "stdout": "ruff 0.14.4",
            "stderr": "",
        },
    )()

    result = check_tool_version("ruff", ["ruff"])

    assert_that(result.name).is_equal_to("ruff")
    assert_that(result.current_version).is_equal_to("0.14.4")
    assert_that(result.min_version).is_equal_to("0.14.0")  # From pyproject.toml
    assert_that(result.version_check_passed).is_true()
    assert_that(result.error_message).is_none()


@patch("subprocess.run")
def test_check_tool_version_failure(mock_run: MagicMock) -> None:
    """Test version check that fails due to old version.

    Args:
        mock_run: Mocked subprocess.run function.
    """
    mock_run.return_value = type(
        "MockResult",
        (),
        {
            "returncode": 0,
            "stdout": "ruff 0.13.0",  # Older than minimum 0.14.0
            "stderr": "",
        },
    )()

    result = check_tool_version("ruff", ["ruff"])

    assert_that(result.name).is_equal_to("ruff")
    assert_that(result.current_version).is_equal_to("0.13.0")
    assert_that(result.min_version).is_equal_to("0.14.0")
    assert_that(result.version_check_passed).is_false()
    assert_that(result.error_message).contains("below minimum requirement")


@patch("subprocess.run")
def test_check_tool_version_command_failure(mock_run: MagicMock) -> None:
    """Test version check when command fails.

    Args:
        mock_run: Mocked subprocess.run function.
    """
    mock_run.side_effect = FileNotFoundError("Command not found")

    result = check_tool_version("nonexistent", ["nonexistent"])

    assert_that(result.name).is_equal_to("nonexistent")
    assert_that(result.current_version).is_none()
    # For tools not in requirements, version check passes (no enforcement)
    assert_that(result.version_check_passed).is_true()
    assert_that(result.error_message).is_not_none()
    assert_that(result.error_message).contains("Failed to run version check")


def test_tool_version_info_creation() -> None:
    """Test ToolVersionInfo dataclass."""
    info = ToolVersionInfo(
        name="test_tool",
        min_version="1.0.0",
        install_hint="Install test_tool",
        current_version="1.2.0",
        version_check_passed=True,
    )

    assert_that(info.name).is_equal_to("test_tool")
    assert_that(info.current_version).is_equal_to("1.2.0")
    assert_that(info.version_check_passed).is_true()


@patch("subprocess.run")
def test_get_all_tool_versions(mock_run: MagicMock) -> None:
    """Test getting versions for all tools.

    Args:
        mock_run: Mocked subprocess.run function.
    """
    # Mock successful version checks for all tools
    mock_run.return_value = type(
        "MockResult",
        (),
        {
            "returncode": 0,
            "stdout": "0.14.4",  # Generic version response
            "stderr": "",
        },
    )()

    results = get_all_tool_versions()

    # Should have results for all supported tools
    expected_tools = {
        "ruff",
        "black",
        "bandit",
        "yamllint",
        "darglint",
        "mypy",
        "pytest",
        "prettier",
        "biome",
        "hadolint",
        "actionlint",
        "markdownlint",
        "clippy",
    }

    assert_that(set(results.keys())).is_equal_to(expected_tools)

    # Each result should be a ToolVersionInfo
    for tool_name, info in results.items():
        assert_that(info).is_instance_of(ToolVersionInfo)
        assert_that(info.name).is_equal_to(tool_name)


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (">=0.14.0", "0.14.0"),
        ("==1.8.1", "1.8.1"),
        (">=25.0.0,<26.0.0", "25.0.0"),
        ("1.0.0", "1.0.0"),  # No operator
    ],
)
def test_parse_version_specifier(specifier: str, expected: str) -> None:
    """Test parsing PEP 508 version specifiers.

    Args:
        specifier: PEP 508 version specifier string.
        expected: Expected parsed version string.
    """
    from lintro.tools.core.version_checking import _parse_version_specifier

    assert_that(_parse_version_specifier(specifier)).is_equal_to(expected)
