"""Tests for config_loader module."""

from pathlib import Path

from lintro.config.config_loader import (
    _convert_pyproject_to_config,
    _find_config_file,
    _parse_execution_config,
    _parse_global_config,
    _parse_tool_config,
    _parse_tools_config,
    clear_config_cache,
    get_config,
    get_default_config,
    load_config,
)


class TestParseGlobalConfig:
    """Tests for _parse_global_config."""

    def test_empty_data(self) -> None:
        """Should return GlobalConfig with None values."""
        config = _parse_global_config({})

        assert config.line_length is None
        assert config.target_python is None

    def test_with_values(self) -> None:
        """Should parse all global values."""
        data = {
            "line_length": 88,
            "target_python": "py313",
            "indent_size": 4,
            "quote_style": "double",
        }

        config = _parse_global_config(data)

        assert config.line_length == 88
        assert config.target_python == "py313"
        assert config.indent_size == 4
        assert config.quote_style == "double"


class TestParseExecutionConfig:
    """Tests for _parse_execution_config."""

    def test_empty_data(self) -> None:
        """Should return defaults."""
        config = _parse_execution_config({})

        assert config.enabled_tools == []
        assert config.tool_order == "priority"
        assert config.fail_fast is False

    def test_with_values(self) -> None:
        """Should parse all execution values."""
        data = {
            "enabled_tools": ["ruff", "prettier"],
            "tool_order": ["prettier", "ruff"],
            "fail_fast": True,
            "parallel": True,
        }

        config = _parse_execution_config(data)

        assert config.enabled_tools == ["ruff", "prettier"]
        assert config.tool_order == ["prettier", "ruff"]
        assert config.fail_fast is True
        assert config.parallel is True

    def test_string_enabled_tools(self) -> None:
        """Should convert single tool string to list."""
        data = {"enabled_tools": "ruff"}

        config = _parse_execution_config(data)

        assert config.enabled_tools == ["ruff"]


class TestParseToolConfig:
    """Tests for _parse_tool_config."""

    def test_empty_data(self) -> None:
        """Should return default ToolConfig."""
        config = _parse_tool_config({})

        assert config.enabled is True
        assert config.config_source is None
        assert config.overrides == {}
        assert config.settings == {}

    def test_with_config_source(self) -> None:
        """Should parse config_source."""
        data = {
            "enabled": True,
            "config_source": ".prettierrc",
        }

        config = _parse_tool_config(data)

        assert config.config_source == ".prettierrc"

    def test_with_overrides(self) -> None:
        """Should parse overrides dict."""
        data = {
            "overrides": {"printWidth": 88},
        }

        config = _parse_tool_config(data)

        assert config.overrides == {"printWidth": 88}

    def test_unknown_keys_become_settings(self) -> None:
        """Unknown keys should become settings."""
        data = {
            "enabled": True,
            "select": ["E", "F"],
            "ignore": ["E501"],
        }

        config = _parse_tool_config(data)

        assert config.settings["select"] == ["E", "F"]
        assert config.settings["ignore"] == ["E501"]


class TestParseToolsConfig:
    """Tests for _parse_tools_config."""

    def test_empty_data(self) -> None:
        """Should return empty dict."""
        config = _parse_tools_config({})

        assert config == {}

    def test_with_tool_dicts(self) -> None:
        """Should parse tool configurations."""
        data = {
            "ruff": {"enabled": True, "select": ["E", "F"]},
            "prettier": {"enabled": False},
        }

        config = _parse_tools_config(data)

        assert "ruff" in config
        assert "prettier" in config
        assert config["ruff"].enabled is True
        assert config["ruff"].settings["select"] == ["E", "F"]
        assert config["prettier"].enabled is False

    def test_with_bool_values(self) -> None:
        """Should handle bool as enabled flag."""
        data = {
            "ruff": True,
            "prettier": False,
        }

        config = _parse_tools_config(data)

        assert config["ruff"].enabled is True
        assert config["prettier"].enabled is False

    def test_case_normalization(self) -> None:
        """Tool names should be lowercased."""
        data = {"RUFF": {"enabled": True}}

        config = _parse_tools_config(data)

        assert "ruff" in config
        assert "RUFF" not in config


class TestConvertPyprojectToConfig:
    """Tests for _convert_pyproject_to_config."""

    def test_empty_data(self) -> None:
        """Should return structure with empty sections."""
        result = _convert_pyproject_to_config({})

        assert "global" in result
        assert "execution" in result
        assert "tools" in result

    def test_global_settings(self) -> None:
        """Should extract global settings."""
        data = {
            "line_length": 88,
            "target_python": "py313",
        }

        result = _convert_pyproject_to_config(data)

        assert result["global"]["line_length"] == 88
        assert result["global"]["target_python"] == "py313"

    def test_tool_sections(self) -> None:
        """Should extract tool-specific sections."""
        data = {
            "ruff": {"select": ["E", "F"]},
            "prettier": {"printWidth": 88},
        }

        result = _convert_pyproject_to_config(data)

        assert result["tools"]["ruff"] == {"select": ["E", "F"]}
        assert result["tools"]["prettier"] == {"printWidth": 88}

    def test_execution_settings(self) -> None:
        """Should extract execution settings."""
        data = {
            "tool_order": "alphabetical",
            "fail_fast": True,
        }

        result = _convert_pyproject_to_config(data)

        assert result["execution"]["tool_order"] == "alphabetical"
        assert result["execution"]["fail_fast"] is True


class TestLoadConfig:
    """Tests for load_config."""

    def test_load_yaml_config(self, tmp_path: Path) -> None:
        """Should load .lintro-config.yaml file."""
        config_content = """\
global:
  line_length: 100

tools:
  ruff:
    enabled: true
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        # Change to temp directory to find config
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            config = load_config()

            assert config.global_config.line_length == 100
            assert config.get_tool_config("ruff").enabled is True
            assert config.config_path is not None
        finally:
            os.chdir(original_cwd)

    def test_load_explicit_path(self, tmp_path: Path) -> None:
        """Should load from explicit path."""
        config_content = """\
global:
  line_length: 120
"""
        config_file = tmp_path / "custom-config.yaml"
        config_file.write_text(config_content)

        config = load_config(config_path=str(config_file))

        assert config.global_config.line_length == 120

    def test_returns_default_when_no_config(self, tmp_path: Path) -> None:
        """Should return default config when no file found."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            config = load_config(allow_pyproject_fallback=False)

            # Should get default empty config
            assert config.global_config.line_length is None
        finally:
            os.chdir(original_cwd)


class TestGetDefaultConfig:
    """Tests for get_default_config."""

    def test_returns_sensible_defaults(self) -> None:
        """Should return config with sensible defaults."""
        config = get_default_config()

        assert config.global_config.line_length == 88
        assert config.global_config.target_python == "py313"
        assert config.execution.tool_order == "priority"


class TestGetConfig:
    """Tests for get_config singleton."""

    def test_caches_config(self, tmp_path: Path) -> None:
        """Should cache loaded config."""
        config_content = """\
global:
  line_length: 88
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            config1 = get_config()
            config2 = get_config()

            assert config1 is config2
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_reload_clears_cache(self, tmp_path: Path) -> None:
        """Should reload when reload=True."""
        config_content = """\
global:
  line_length: 88
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            config1 = get_config()

            # Modify config file
            config_file.write_text(
                """\
global:
  line_length: 120
"""
            )

            # Without reload, should get cached value
            config2 = get_config()
            assert config2.global_config.line_length == 88

            # With reload, should get new value
            config3 = get_config(reload=True)
            assert config3.global_config.line_length == 120
        finally:
            os.chdir(original_cwd)
            clear_config_cache()


class TestFindConfigFile:
    """Tests for _find_config_file."""

    def test_finds_in_current_dir(self, tmp_path: Path) -> None:
        """Should find config in current directory."""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text("global: {}")

        result = _find_config_file(start_dir=tmp_path)

        assert result == config_file

    def test_finds_in_parent_dir(self, tmp_path: Path) -> None:
        """Should find config in parent directory."""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text("global: {}")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = _find_config_file(start_dir=subdir)

        assert result == config_file

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """Should return None when no config found."""
        result = _find_config_file(start_dir=tmp_path)

        assert result is None

    def test_supports_alternate_names(self, tmp_path: Path) -> None:
        """Should find alternate config file names."""
        # Try .yml extension
        config_file = tmp_path / ".lintro-config.yml"
        config_file.write_text("global: {}")

        result = _find_config_file(start_dir=tmp_path)

        assert result == config_file
