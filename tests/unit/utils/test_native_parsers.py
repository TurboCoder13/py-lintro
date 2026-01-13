"""Unit tests for native_parsers.py error handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_json_config, _load_native_tool_config

# =============================================================================
# _load_json_config - Error Handling
# =============================================================================


def test_load_json_config_parse_error_logs_warning(tmp_path: Path) -> None:
    """Verify JSON parse error logs warning with details.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    config_file = tmp_path / "bad.json"
    config_file.write_text("{ invalid json }")

    with patch("lintro.utils.native_parsers.logger") as mock_logger:
        result = _load_json_config(config_file)

        assert_that(result).is_equal_to({})
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert_that(warning_msg).contains("Failed to parse JSON config")
        assert_that(warning_msg).contains(str(config_file))


def test_load_json_config_file_not_found_logs_debug(tmp_path: Path) -> None:
    """Verify missing file logs debug message.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    missing_file = tmp_path / "missing.json"

    with patch("lintro.utils.native_parsers.logger") as mock_logger:
        result = _load_json_config(missing_file)

        assert_that(result).is_equal_to({})
        mock_logger.debug.assert_called_once()
        debug_msg = mock_logger.debug.call_args[0][0]
        assert_that(debug_msg).contains("Config file not found")


def test_load_json_config_valid_returns_dict(tmp_path: Path) -> None:
    """Verify valid JSON returns parsed dict.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    config_file = tmp_path / "valid.json"
    config_file.write_text('{"key": "value"}')

    result = _load_json_config(config_file)

    assert_that(result).is_equal_to({"key": "value"})


def test_load_json_config_non_dict_returns_empty(tmp_path: Path) -> None:
    """Verify non-dict JSON returns empty dict.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    config_file = tmp_path / "array.json"
    config_file.write_text('["item1", "item2"]')

    result = _load_json_config(config_file)

    assert_that(result).is_equal_to({})


# =============================================================================
# _load_native_tool_config - YAML Parse Errors (yamllint)
# =============================================================================


def test_load_yamllint_config_yaml_error_logs_warning() -> None:
    """Verify YAML parse error for yamllint config logs warning."""
    with (
        patch("lintro.utils.native_parsers.Path.exists", return_value=True),
        patch(
            "builtins.open",
            mock_open(read_data="invalid: yaml: content: ["),
        ),
        patch("lintro.utils.native_parsers.yaml") as mock_yaml,
        patch("lintro.utils.native_parsers.logger") as mock_logger,
    ):
        # Make yaml.YAMLError available for isinstance check
        mock_yaml.YAMLError = type("YAMLError", (Exception,), {})
        mock_yaml.safe_load.side_effect = mock_yaml.YAMLError("bad yaml")

        result = _load_native_tool_config("yamllint")

        assert_that(result).is_equal_to({})
        mock_logger.warning.assert_called()


def test_load_yamllint_config_os_error_returns_empty() -> None:
    """Verify OS error reading yamllint config returns empty dict."""
    with (
        patch("lintro.utils.native_parsers.Path.exists", return_value=True),
        patch("builtins.open", side_effect=OSError("Permission denied")),
        patch("lintro.utils.native_parsers.yaml") as mock_yaml,
    ):
        mock_yaml.YAMLError = type("YAMLError", (Exception,), {})

        result = _load_native_tool_config("yamllint")

        # OS errors should return empty dict gracefully
        assert_that(result).is_equal_to({})


# =============================================================================
# _load_native_tool_config - Prettier Parse Errors
# =============================================================================


def test_load_prettier_package_json_parse_error_logs_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify JSON parse error in package.json logs warning.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Create package.json with invalid JSON
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text("{ invalid json }")

    # Change to temp directory so Path("package.json") finds our file
    monkeypatch.chdir(tmp_path)

    with patch("lintro.utils.native_parsers.logger") as mock_logger:
        result = _load_native_tool_config("prettier")

        assert_that(result).is_equal_to({})
        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert_that(warning_msg).contains("Failed to parse prettier config")


# =============================================================================
# _load_native_tool_config - Biome Parse Errors
# =============================================================================


def test_load_biome_config_parse_error_logs_warning() -> None:
    """Verify JSON parse error in biome.json logs warning."""
    with (
        patch("lintro.utils.native_parsers.Path.exists", return_value=True),
        patch(
            "lintro.utils.native_parsers.Path.read_text",
            return_value="{ bad json }",
        ),
        patch("lintro.utils.native_parsers.logger") as mock_logger,
    ):
        result = _load_native_tool_config("biome")

        assert_that(result).is_equal_to({})
        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert_that(warning_msg).contains("Failed to parse Biome config")


# =============================================================================
# _load_native_tool_config - Markdownlint Parse Errors
# =============================================================================


def test_load_markdownlint_missing_config_returns_empty() -> None:
    """Verify missing markdownlint config returns empty dict."""
    with patch("lintro.utils.native_parsers.Path.exists", return_value=False):
        result = _load_native_tool_config("markdownlint")
        assert_that(result).is_equal_to({})
