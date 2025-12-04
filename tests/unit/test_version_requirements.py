"""Tests for version requirements functionality."""

from unittest.mock import patch

import pytest

from lintro.tools.core.version_requirements import (
    ToolVersionInfo,
    _compare_versions,
    _extract_version_from_output,
    _get_install_hints,
    _get_minimum_versions,
    _parse_version,
    check_tool_version,
    get_all_tool_versions,
    get_install_hints,
    get_minimum_versions,
)


@pytest.mark.parametrize(
    "version_str,expected",
    [
        ("1.2.3", (1, 2, 3)),
        ("0.14.0", (0, 14, 0)),
        ("2.0", (2, 0)),
        ("1.0.0-alpha", (1, 0, 0)),  # Should handle pre-release
        ("invalid", (0,)),  # Should return default for invalid
    ],
)
def test_parse_version(version_str, expected):
    """Test version string parsing.

    Args:
        version_str: Version string to parse.
        expected: Expected parsed version tuple.
    """
    assert _parse_version(version_str) == expected


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
def test_compare_versions(version1, version2, expected):
    """Test version comparison.

    Args:
        version1: First version string to compare.
        version2: Second version string to compare.
        expected: Expected comparison result (-1, 0, or 1).
    """
    assert _compare_versions(version1, version2) == expected


@pytest.mark.parametrize(
    "tool_name,output,expected",
    [
        ("black", "black, 25.9.0 (compiled: yes)", "25.9.0"),
        ("bandit", "__main__.py 1.8.6", "1.8.6"),
        ("hadolint", "Haskell Dockerfile Linter 2.14.0", "2.14.0"),
        ("prettier", "Prettier 3.7.3", "3.7.3"),
        ("actionlint", "actionlint 1.7.5", "1.7.5"),
        ("darglint", "1.8.1", "1.8.1"),
        ("ruff", "ruff 0.14.4", "0.14.4"),
        ("yamllint", "yamllint 1.37.1", "1.37.1"),
    ],
)
def test_extract_version_from_output(tool_name, output, expected):
    """Test version extraction from various tool outputs.

    Args:
        tool_name: Name of the tool.
        output: Raw version output string from tool.
        expected: Expected extracted version string.
    """
    assert _extract_version_from_output(output, tool_name) == expected


def test_get_minimum_versions_from_pyproject():
    """Test reading minimum versions from pyproject.toml."""
    versions = _get_minimum_versions()

    # Should include bundled tools from dependencies
    assert "ruff" in versions
    assert "black" in versions
    assert "bandit" in versions
    assert "yamllint" in versions
    assert "darglint" in versions

    # Should include tools from [tool.lintro.versions]
    assert "prettier" in versions
    assert "hadolint" in versions
    assert "actionlint" in versions
    assert "pytest" in versions

    # Versions should be strings
    assert isinstance(versions["ruff"], str)
    assert isinstance(versions["prettier"], str)


def test_get_install_hints():
    """Test generating install hints."""
    hints = _get_install_hints()

    assert "ruff" in hints
    assert "prettier" in hints
    assert "Install via:" in hints["ruff"]
    assert "npm install" in hints["prettier"]


def test_version_caching():
    """Test that versions are cached properly."""
    # First call
    versions1 = get_minimum_versions()
    hints1 = get_install_hints()

    # Second call should return same objects (cached)
    versions2 = get_minimum_versions()
    hints2 = get_install_hints()

    assert versions1 is versions2
    assert hints1 is hints2


@patch("subprocess.run")
def test_check_tool_version_success(mock_run):
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

    assert result.name == "ruff"
    assert result.current_version == "0.14.4"
    assert result.min_version == "0.14.0"  # From pyproject.toml
    assert result.version_check_passed is True
    assert result.error_message is None


@patch("subprocess.run")
def test_check_tool_version_failure(mock_run):
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

    assert result.name == "ruff"
    assert result.current_version == "0.13.0"
    assert result.min_version == "0.14.0"
    assert result.version_check_passed is False
    assert "below minimum requirement" in result.error_message


@patch("subprocess.run")
def test_check_tool_version_command_failure(mock_run):
    """Test version check when command fails.

    Args:
        mock_run: Mocked subprocess.run function.
    """
    mock_run.side_effect = FileNotFoundError("Command not found")

    result = check_tool_version("nonexistent", ["nonexistent"])

    assert result.name == "nonexistent"
    assert result.current_version is None
    # For tools not in requirements, version check passes (no enforcement)
    assert result.version_check_passed is True
    assert result.error_message is not None
    assert "Failed to run version check" in result.error_message


def test_tool_version_info_creation():
    """Test ToolVersionInfo dataclass."""
    info = ToolVersionInfo(
        name="test_tool",
        min_version="1.0.0",
        install_hint="Install test_tool",
        current_version="1.2.0",
        version_check_passed=True,
    )

    assert info.name == "test_tool"
    assert info.current_version == "1.2.0"
    assert info.version_check_passed is True


@patch("subprocess.run")
def test_get_all_tool_versions(mock_run):
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
        "pytest",
        "prettier",
        "hadolint",
        "actionlint",
        "markdownlint",
    }

    assert set(results.keys()) == expected_tools

    # Each result should be a ToolVersionInfo
    for tool_name, info in results.items():
        assert isinstance(info, ToolVersionInfo)
        assert info.name == tool_name


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (">=0.14.0", "0.14.0"),
        ("==1.8.1", "1.8.1"),
        (">=25.0.0,<26.0.0", "25.0.0"),
        ("1.0.0", "1.0.0"),  # No operator
    ],
)
def test_parse_version_specifier(specifier, expected):
    """Test parsing PEP 508 version specifiers.

    Args:
        specifier: PEP 508 version specifier string.
        expected: Expected parsed version string.
    """
    from lintro.tools.core.version_requirements import _parse_version_specifier

    assert _parse_version_specifier(specifier) == expected
