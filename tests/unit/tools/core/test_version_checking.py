"""Unit tests for version_checking module."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, _patch, patch

import pytest
from assertpy import assert_that

from lintro.tools.core.version_checking import (
    _get_version_timeout,
    _load_pyproject_config,
    _parse_version_specifier,
    get_install_hints,
    get_minimum_versions,
)

# Fixtures


@pytest.fixture
def mock_path_not_found() -> MagicMock:
    """Create a mock path that simulates pyproject.toml not found.

    Returns:
        A MagicMock configured to simulate a missing pyproject.toml file.
    """
    mock_current = MagicMock()
    mock_file = MagicMock()
    mock_file.exists.return_value = False
    mock_current.__truediv__ = MagicMock(return_value=mock_file)
    mock_current.parents = []
    return mock_current


@pytest.fixture
def mock_empty_config() -> Iterator[None]:
    """Patch _load_pyproject_config to return empty dict.

    Yields:
        None: No value yielded, just provides context.
    """
    with patch(
        "lintro.tools.core.version_checking._load_pyproject_config",
        return_value={},
    ):
        yield


@pytest.fixture
def mock_minimum_versions() -> Callable[[dict[str, str]], _patch[Any]]:
    """Factory fixture for mocking get_minimum_versions.

    Returns:
        A factory function for creating version patches.
    """

    def _mock(versions: dict[str, str]) -> _patch[Any]:
        return patch(
            "lintro.tools.core.version_checking.get_minimum_versions",
            return_value=versions,
        )

    return _mock


# Tests for _get_version_timeout


def test_get_version_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return default timeout when env var not set.

    Args:
        monkeypatch: Pytest fixture for patching modules and attributes.
    """
    monkeypatch.delenv("LINTRO_VERSION_TIMEOUT", raising=False)
    result = _get_version_timeout()
    assert_that(result).is_equal_to(30)


def test_get_version_timeout_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return parsed timeout from env var.

    Args:
        monkeypatch: Pytest fixture for patching modules and attributes.
    """
    monkeypatch.setenv("LINTRO_VERSION_TIMEOUT", "60")
    result = _get_version_timeout()
    assert_that(result).is_equal_to(60)


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("invalid", 30),
        ("-5", 30),
        ("0", 30),
    ],
    ids=["non_numeric", "negative", "zero"],
)
def test_get_version_timeout_invalid(
    env_value: str,
    expected: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return default on invalid timeout values.

    Args:
        env_value: The environment variable value to test.
        expected: The expected timeout value.
        monkeypatch: Pytest monkeypatch fixture for environment manipulation.
    """
    monkeypatch.setenv("LINTRO_VERSION_TIMEOUT", env_value)
    result = _get_version_timeout()
    assert_that(result).is_equal_to(expected)


# Tests for _load_pyproject_config


def test_load_pyproject_config_success(tmp_path: Path) -> None:
    """Load pyproject.toml successfully.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.lintro]\nline_length = 100\n")

    with patch("lintro.tools.core.version_checking.Path") as mock_path:
        mock_current = MagicMock()
        mock_path.return_value = mock_current
        mock_current.__truediv__ = MagicMock(return_value=pyproject)
        mock_current.parents = []

        with patch("os.path.dirname", return_value=str(tmp_path)):
            result = _load_pyproject_config()

    assert_that(result).is_instance_of(dict)


def test_load_pyproject_config_not_found(mock_path_not_found: MagicMock) -> None:
    """Return empty dict when pyproject.toml not found.

    Args:
        mock_path_not_found: Mock fixture for missing pyproject.toml.
    """
    with patch("lintro.tools.core.version_checking.Path") as mock_path:
        mock_path.return_value = mock_path_not_found

        with patch("os.path.dirname", return_value="/nonexistent"):
            result = _load_pyproject_config()

    assert_that(result).is_empty()


# Tests for _parse_version_specifier


@pytest.mark.parametrize(
    ("specifier", "expected"),
    [
        (">=1.0.0", "1.0.0"),
        ("==1.8.1", "1.8.1"),
        ("~=2.5.0", "2.5.0"),
        (">1.0.0", "1.0.0"),
        (">=1.0.0,<2.0.0", "1.0.0"),
        ("package[extra]>=1.5.0", "1.5.0"),
        (">=1.0.0; python_version>='3.8'", "1.0.0"),
    ],
    ids=[
        "greater_equal",
        "equal_equal",
        "tilde_equal",
        "greater_than",
        "multiple_constraints",
        "with_extras",
        "with_markers",
    ],
)
def test_parse_version_specifier(specifier: str, expected: str) -> None:
    """Parse version specifier and return version string.

    Args:
        specifier: The version specifier string to parse.
        expected: The expected parsed version string.
    """
    result = _parse_version_specifier(specifier)
    assert_that(result).is_equal_to(expected)


@pytest.mark.parametrize(
    ("specifier", "expected"),
    [
        (
            "package @ https://example.com/pkg.whl",
            "package @ https://example.com/pkg.whl",
        ),
        ("package[extra]", "package[extra]"),
    ],
    ids=["url_dependency", "extras_without_version"],
)
def test_parse_version_specifier_passthrough(specifier: str, expected: str) -> None:
    """Return original string when no version can be parsed.

    Args:
        specifier: The version specifier string to parse.
        expected: The expected result when parsing fails.
    """
    result = _parse_version_specifier(specifier)
    assert_that(result).is_equal_to(expected)


# Tests for get_minimum_versions


def test_get_minimum_versions_defaults(mock_empty_config: None) -> None:
    """Return default versions when no config found.

    Args:
        mock_empty_config: Fixture that mocks empty config.
    """
    result = get_minimum_versions()
    assert_that("pytest" in result).is_true()
    assert_that("prettier" in result).is_true()


def test_get_minimum_versions_bundled_tools() -> None:
    """Parse bundled tool versions from dependencies."""
    config = {
        "project": {
            "dependencies": [
                "ruff>=0.8.0",
                "black>=24.0.0",
            ],
        },
    }
    with patch(
        "lintro.tools.core.version_checking._load_pyproject_config",
        return_value=config,
    ):
        result = get_minimum_versions()
        assert_that(result.get("ruff")).is_equal_to("0.8.0")
        assert_that(result.get("black")).is_equal_to("24.0.0")


def test_get_minimum_versions_bundled_tools_with_extras() -> None:
    """Parse bundled tool versions with extras."""
    config = {
        "project": {
            "dependencies": [
                "bandit[toml]>=1.7.0",
            ],
        },
    }
    with patch(
        "lintro.tools.core.version_checking._load_pyproject_config",
        return_value=config,
    ):
        result = get_minimum_versions()
        assert_that(result.get("bandit")).is_equal_to("1.7.0")


def test_get_minimum_versions_lintro_section() -> None:
    """Read versions from [tool.lintro.versions] section."""
    config = {
        "tool": {
            "lintro": {
                "versions": {
                    "prettier": "4.0.0",
                    "custom_tool": "1.0.0",
                },
            },
        },
    }
    with patch(
        "lintro.tools.core.version_checking._load_pyproject_config",
        return_value=config,
    ):
        result = get_minimum_versions()
        assert_that(result.get("prettier")).is_equal_to("4.0.0")
        assert_that(result.get("custom_tool")).is_equal_to("1.0.0")


# Tests for get_install_hints


def test_get_install_hints_all_tools(
    mock_minimum_versions: Callable[[dict[str, str]], _patch[Any]],
) -> None:
    """Return install hints for all tools.

    Args:
        mock_minimum_versions: Factory fixture for mocking versions.
    """
    with mock_minimum_versions(
        {
            "ruff": "0.8.0",
            "pytest": "8.0.0",
            "prettier": "3.7.0",
        },
    ):
        result = get_install_hints()
        assert_that("ruff" in result).is_true()
        assert_that("pytest" in result).is_true()
        assert_that("prettier" in result).is_true()


def test_get_install_hints_pip_for_python_tools(
    mock_minimum_versions: Callable[[dict[str, str]], _patch[Any]],
) -> None:
    """Python tools have pip/uv install hints.

    Args:
        mock_minimum_versions: Factory fixture for mocking versions.
    """
    with mock_minimum_versions({"ruff": "0.8.0"}):
        result = get_install_hints()
        assert_that("pip install" in result.get("ruff", "")).is_true()
        assert_that("uv add" in result.get("ruff", "")).is_true()


def test_get_install_hints_bun_for_node_tools(
    mock_minimum_versions: Callable[[dict[str, str]], _patch[Any]],
) -> None:
    """Node.js tools have bun install hints.

    Args:
        mock_minimum_versions: Factory fixture for mocking versions.
    """
    with mock_minimum_versions({"prettier": "3.7.0"}):
        result = get_install_hints()
        assert_that("bun add" in result.get("prettier", "")).is_true()


def test_get_install_hints_external_tools(
    mock_minimum_versions: Callable[[dict[str, str]], _patch[Any]],
) -> None:
    """External tools have appropriate install hints.

    Args:
        mock_minimum_versions: Factory fixture for mocking versions.
    """
    with mock_minimum_versions(
        {
            "hadolint": "2.12.0",
            "clippy": "1.75.0",
        },
    ):
        result = get_install_hints()
        assert_that("github" in result.get("hadolint", "").lower()).is_true()
        assert_that("rustup" in result.get("clippy", "")).is_true()
