"""Tests for _load_native_tool_config with oxlint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_oxlint_config_from_oxlintrc_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load oxlint config from .oxlintrc.json file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config = {"rules": {"no-debugger": "error"}}
    (temp_cwd / ".oxlintrc.json").write_text('{"rules": {"no-debugger": "error"}}')

    result = _load_native_tool_config("oxlint")

    assert_that(result).is_equal_to(config)


def test_load_oxlint_config_from_oxlint_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load oxlint config from oxlint.json file (alternative name).

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config = {"plugins": ["react"], "rules": {"eqeqeq": "warn"}}
    (temp_cwd / "oxlint.json").write_text(
        '{"plugins": ["react"], "rules": {"eqeqeq": "warn"}}',
    )

    result = _load_native_tool_config("oxlint")

    assert_that(result).is_equal_to(config)


def test_load_oxlint_config_prefers_oxlintrc_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Prefer .oxlintrc.json over oxlint.json when both exist.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxlintrc.json").write_text('{"source": "oxlintrc"}')
    (temp_cwd / "oxlint.json").write_text('{"source": "oxlint"}')

    result = _load_native_tool_config("oxlint")

    assert_that(result).is_equal_to({"source": "oxlintrc"})


def test_load_oxlint_config_no_config_file(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when no oxlint config file exists.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    result = _load_native_tool_config("oxlint")

    assert_that(result).is_empty()


def test_load_oxlint_config_invalid_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when oxlint config contains invalid JSON.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxlintrc.json").write_text("{ invalid json }")

    result = _load_native_tool_config("oxlint")

    assert_that(result).is_empty()


def test_load_oxlint_config_non_dict_returns_empty(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when oxlint config is not a dict.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxlintrc.json").write_text('["not", "a", "dict"]')

    result = _load_native_tool_config("oxlint")

    assert_that(result).is_empty()
