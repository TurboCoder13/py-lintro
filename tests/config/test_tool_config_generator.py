"""Tests for tool_config_generator module."""

from assertpy import assert_that

from lintro.config.enforce_config import EnforceConfig
from lintro.config.lintro_config import LintroConfig
from lintro.config.tool_config_generator import (
    _convert_python_version_for_mypy,
    _write_defaults_config,
    get_defaults_injection_args,
    get_enforce_cli_args,
)
from lintro.enums.config_format import ConfigFormat


def test_returns_empty_when_no_enforce_settings() -> None:
    """Should return empty list when no enforce settings."""
    lintro_config = LintroConfig()

    args = get_enforce_cli_args(
        tool_name="ruff",
        lintro_config=lintro_config,
    )

    assert_that(args).is_empty()


def test_injects_line_length_for_black() -> None:
    """Should inject --line-length for black."""
    lintro_config = LintroConfig(
        enforce=EnforceConfig(line_length=88),
    )

    args = get_enforce_cli_args(
        tool_name="black",
        lintro_config=lintro_config,
    )

    assert_that(args).is_equal_to(["--line-length", "88"])


def test_injects_target_version_for_ruff() -> None:
    """Should inject --target-version for ruff."""
    lintro_config = LintroConfig(
        enforce=EnforceConfig(target_python="py312"),
    )

    args = get_enforce_cli_args(
        tool_name="ruff",
        lintro_config=lintro_config,
    )

    assert_that(args).is_equal_to(["--target-version", "py312"])


def test_injects_both_line_length_and_target_version() -> None:
    """Should inject both settings when both are set."""
    lintro_config = LintroConfig(
        enforce=EnforceConfig(
            line_length=100,
            target_python="py313",
        ),
    )

    args = get_enforce_cli_args(
        tool_name="ruff",
        lintro_config=lintro_config,
    )

    assert_that(args).contains("--line-length")
    assert_that(args).contains("100")
    assert_that(args).contains("--target-version")
    assert_that(args).contains("py313")


def test_converts_target_version_format_for_mypy() -> None:
    """Should convert py313 format to 3.13 for mypy."""
    lintro_config = LintroConfig(
        enforce=EnforceConfig(target_python="py313"),
    )

    args = get_enforce_cli_args(
        tool_name="mypy",
        lintro_config=lintro_config,
    )

    assert_that(args).is_equal_to(["--python-version", "3.13"])


def test_convert_python_version_helper_handles_plain_version() -> None:
    """Should return plain version unchanged when already numeric."""
    assert_that(_convert_python_version_for_mypy("3.12")).is_equal_to("3.12")


def test_returns_empty_for_unsupported_tool() -> None:
    """Should return empty list for tools without CLI mappings."""
    lintro_config = LintroConfig(
        enforce=EnforceConfig(line_length=100),
    )

    args = get_enforce_cli_args(
        tool_name="yamllint",
        lintro_config=lintro_config,
    )

    # yamllint doesn't support --line-length CLI flag
    assert_that(args).is_empty()


def test_returns_empty_for_none_path() -> None:
    """Should return empty list when no config path."""
    args = get_defaults_injection_args(
        tool_name="prettier",
        config_path=None,
    )

    assert_that(args).is_empty()


def test_markdownlint_config_uses_correct_suffix() -> None:
    """Should use .markdownlint-cli2.jsonc suffix for markdownlint.

    markdownlint-cli2 v0.17+ requires config files to follow strict naming
    conventions. The temp config file must end with a recognized suffix.
    """
    config_path = _write_defaults_config(
        defaults={"config": {"MD013": {"line_length": 100}}},
        tool_name="markdownlint",
        config_format=ConfigFormat.JSON,
    )

    try:
        assert_that(str(config_path)).ends_with(".markdownlint-cli2.jsonc")
        assert_that(config_path.exists()).is_true()
    finally:
        config_path.unlink(missing_ok=True)


def test_generic_tool_config_uses_json_suffix() -> None:
    """Should use .json suffix for tools without special requirements."""
    config_path = _write_defaults_config(
        defaults={"some": "config"},
        tool_name="prettier",
        config_format=ConfigFormat.JSON,
    )

    try:
        assert_that(str(config_path)).ends_with(".json")
        assert_that(config_path.exists()).is_true()
    finally:
        config_path.unlink(missing_ok=True)
