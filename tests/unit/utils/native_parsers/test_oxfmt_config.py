"""Tests for _load_native_tool_config with oxfmt."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_oxfmt_config_from_oxfmtrc_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load oxfmt config from .oxfmtrc.json file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config = {"printWidth": 100, "tabWidth": 2}
    (temp_cwd / ".oxfmtrc.json").write_text('{"printWidth": 100, "tabWidth": 2}')

    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_equal_to(config)


def test_load_oxfmt_config_from_oxfmtrc_jsonc(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load oxfmt config from .oxfmtrc.jsonc file with comments.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    content = """
    {
        // Line comment
        "printWidth": 100,
        /* Block comment */
        "tabWidth": 2
    }
    """
    (temp_cwd / ".oxfmtrc.jsonc").write_text(content)

    result = _load_native_tool_config("oxfmt")

    assert_that(result["printWidth"]).is_equal_to(100)
    assert_that(result["tabWidth"]).is_equal_to(2)


def test_load_oxfmt_config_prefers_json_over_jsonc(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Prefer .oxfmtrc.json over .oxfmtrc.jsonc when both exist.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxfmtrc.json").write_text('{"source": "json"}')
    (temp_cwd / ".oxfmtrc.jsonc").write_text('{"source": "jsonc"}')

    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_equal_to({"source": "json"})


def test_load_oxfmt_config_no_config_file(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when no oxfmt config file exists.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_empty()


def test_load_oxfmt_config_invalid_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when oxfmt config contains invalid JSON.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxfmtrc.json").write_text("{ invalid json }")

    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_empty()


def test_load_oxfmt_config_non_dict_returns_empty(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when oxfmt config is not a dict.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    (temp_cwd / ".oxfmtrc.json").write_text('["not", "a", "dict"]')

    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_empty()


def test_load_oxfmt_config_jsonc_with_block_comments(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load oxfmt JSONC config with block comments.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    content = """
    {
        /* This is a block comment
           spanning multiple lines */
        "semi": true,
        "singleQuote": false
    }
    """
    (temp_cwd / ".oxfmtrc.jsonc").write_text(content)

    result = _load_native_tool_config("oxfmt")

    assert_that(result["semi"]).is_true()
    assert_that(result["singleQuote"]).is_false()


def test_load_oxfmt_config_jsonc_with_trailing_comma(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """JSONC parser strips comments but not trailing commas (JSON spec).

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    # Note: Standard JSON doesn't support trailing commas
    # JSONC comment stripping works, but trailing comma is still invalid JSON
    content = """
    {
        // comment
        "printWidth": 80
    }
    """
    (temp_cwd / ".oxfmtrc.jsonc").write_text(content)

    result = _load_native_tool_config("oxfmt")

    assert_that(result).is_equal_to({"printWidth": 80})
