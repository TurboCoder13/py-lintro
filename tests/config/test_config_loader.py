"""Tests for config_loader module."""

from pathlib import Path

from assertpy import assert_that

from lintro.config.config_loader import (
    _convert_pyproject_to_config,
    _parse_defaults,
    _parse_enforce_config,
    _parse_execution_config,
    _parse_tool_config,
    _parse_tools_config,
    clear_config_cache,
    get_default_config,
    load_config,
)


def test_empty_data() -> None:
    """Should return EnforceConfig with None values."""
    config = _parse_enforce_config({})

    assert config.line_length is None
    assert config.target_python is None


def test_execution_config_empty_data() -> None:
    """Should return execution config defaults."""
    config = _parse_execution_config({})

    assert_that(config.enabled_tools).is_equal_to([])
    assert_that(config.tool_order).is_equal_to("priority")
    assert config.fail_fast is False
    assert config.parallel is False


def test_string_enabled_tools() -> None:
    """Should convert single tool string to list."""
    data = {"enabled_tools": "ruff"}

    config = _parse_execution_config(data)

    assert_that(config.enabled_tools).is_equal_to(["ruff"])


def test_tool_config_empty_data() -> None:
    """Should return default ToolConfig."""
    config = _parse_tool_config({})

    assert config.enabled is True
    assert config.config_source is None


def test_disabled_tool() -> None:
    """Should parse enabled=False."""
    data = {"enabled": False}

    config = _parse_tool_config(data)

    assert config.enabled is False


def test_tools_config_empty_data() -> None:
    """Should return empty dict for tools config."""
    config = _parse_tools_config({})

    assert_that(config).is_equal_to({})


def test_with_bool_values() -> None:
    """Should handle bool as enabled flag."""
    data = {
        "ruff": True,
        "prettier": False,
    }

    config = _parse_tools_config(data)

    assert config["ruff"].enabled is True
    assert config["prettier"].enabled is False


def test_defaults_empty_data() -> None:
    """Should return empty dict for defaults."""
    defaults = _parse_defaults({})

    assert_that(defaults).is_equal_to({})


def test_case_normalization() -> None:
    """Tool names should be lowercased."""
    data = {"PRETTIER": {"singleQuote": True}}

    defaults = _parse_defaults(data)

    assert_that(defaults).contains("prettier")
    assert "PRETTIER" not in defaults


def test_convert_pyproject_empty_data() -> None:
    """Should return structure with empty sections."""
    result = _convert_pyproject_to_config({})

    assert_that(result).contains("enforce")
    assert_that(result).contains("execution")
    assert_that(result).contains("defaults")
    assert_that(result).contains("tools")


def test_enforce_settings() -> None:
    """Should extract enforce settings."""
    data = {
        "line_length": 88,
        "target_python": "py313",
    }

    result = _convert_pyproject_to_config(data)

    assert result["enforce"]["line_length"] == 88
    assert result["enforce"]["target_python"] == "py313"


def test_tool_sections() -> None:
    """Should extract tool-specific sections."""
    data = {
        "ruff": {"enabled": True},
        "prettier": {"enabled": False},
    }

    result = _convert_pyproject_to_config(data)

    assert result["tools"]["ruff"] == {"enabled": True}
    assert result["tools"]["prettier"] == {"enabled": False}


def test_execution_settings() -> None:
    """Should extract execution settings."""
    data = {
        "tool_order": "alphabetical",
        "fail_fast": True,
    }

    result = _convert_pyproject_to_config(data)

    assert result["execution"]["tool_order"] == "alphabetical"
    assert result["execution"]["fail_fast"] is True


def test_load_yaml_config_with_defaults(tmp_path: Path) -> None:
    """Should load .lintro-config.yaml file with defaults section.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_content = """\
defaults:
  prettier:
    singleQuote: true
    tabWidth: 2
"""
    config_file = tmp_path / ".lintro-config.yaml"
    config_file.write_text(config_content)

    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        clear_config_cache()

        config = load_config()

        assert config.get_tool_defaults("prettier")["singleQuote"] is True
        assert config.get_tool_defaults("prettier")["tabWidth"] == 2
    finally:
        os.chdir(original_cwd)


def test_load_explicit_path(tmp_path: Path) -> None:
    """Should load from explicit path.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_content = """\
enforce:
  line_length: 120
"""
    config_file = tmp_path / "custom-config.yaml"
    config_file.write_text(config_content)

    config = load_config(config_path=str(config_file))

    assert config.enforce.line_length == 120


def test_returns_default_when_no_config(tmp_path: Path) -> None:
    """Should return default config when no file found.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        clear_config_cache()

        config = load_config(allow_pyproject_fallback=False)

        # Should get default empty config
        assert config.enforce.line_length is None
    finally:
        os.chdir(original_cwd)


def test_returns_sensible_defaults() -> None:
    """Should return config with sensible defaults."""
    config = get_default_config()

    assert config.enforce.line_length == 88
    # target_python is None to let tools infer from requires-python
    assert config.enforce.target_python is None
    assert config.execution.tool_order == "priority"
