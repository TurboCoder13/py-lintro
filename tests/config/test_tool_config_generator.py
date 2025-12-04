"""Tests for tool_config_generator module."""

import json
from pathlib import Path

from lintro.config.lintro_config import GlobalConfig, LintroConfig, ToolConfig
from lintro.config.tool_config_generator import (
    _apply_global_settings,
    _merge_tool_settings,
    cleanup_temp_config,
    generate_tool_config,
    get_config_injection_args,
    get_no_auto_config_args,
)


class TestApplyGlobalSettings:
    """Tests for _apply_global_settings."""

    def test_applies_line_length_to_ruff(self) -> None:
        """Should map line_length to ruff's line-length."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=100),
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="ruff",
        )

        assert result["line-length"] == 100

    def test_applies_line_length_to_prettier(self) -> None:
        """Should map line_length to prettier's printWidth."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=120),
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="prettier",
        )

        assert result["printWidth"] == 120

    def test_applies_line_length_to_yamllint(self) -> None:
        """Should map line_length to yamllint's nested rules structure."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=100),
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="yamllint",
        )

        assert result["rules"]["line-length"]["max"] == 100

    def test_applies_line_length_to_markdownlint(self) -> None:
        """Should map line_length to markdownlint's MD013 rule."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=100),
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="markdownlint",
        )

        assert result["MD013"]["line_length"] == 100
        assert result["MD013"]["code_blocks"] is False
        assert result["MD013"]["tables"] is False

    def test_applies_target_python(self) -> None:
        """Should map target_python to ruff and black."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(target_python="py312"),
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="ruff",
        )

        assert result["target-version"] == "py312"

    def test_uses_tool_override_over_global(self) -> None:
        """Should use tool override over global setting."""
        config: dict = {}
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=88),
            tools={
                "ruff": ToolConfig(overrides={"line_length": 120}),
            },
        )

        result = _apply_global_settings(
            config=config,
            lintro_config=lintro_config,
            tool_name="ruff",
        )

        # Should use override (120) not global (88)
        assert result["line-length"] == 120


class TestMergeToolSettings:
    """Tests for _merge_tool_settings."""

    def test_empty_settings(self) -> None:
        """Should return base config unchanged."""
        base = {"a": 1}
        tool_config = ToolConfig()

        result = _merge_tool_settings(
            base_config=base,
            tool_config=tool_config,
        )

        assert result == {"a": 1}

    def test_merges_settings(self) -> None:
        """Should merge settings into base."""
        base = {"a": 1}
        tool_config = ToolConfig(settings={"b": 2})

        result = _merge_tool_settings(
            base_config=base,
            tool_config=tool_config,
        )

        assert result == {"a": 1, "b": 2}

    def test_overrides_win(self) -> None:
        """Overrides should take precedence over settings."""
        base = {"a": 1}
        tool_config = ToolConfig(
            settings={"a": 2, "b": 3},
            overrides={"a": 10},
        )

        result = _merge_tool_settings(
            base_config=base,
            tool_config=tool_config,
        )

        assert result["a"] == 10
        assert result["b"] == 3

    def test_deep_merges_dicts(self) -> None:
        """Should deep merge nested dicts."""
        base = {"rules": {"a": 1}}
        tool_config = ToolConfig(settings={"rules": {"b": 2}})

        result = _merge_tool_settings(
            base_config=base,
            tool_config=tool_config,
        )

        assert result["rules"] == {"a": 1, "b": 2}


class TestGetConfigInjectionArgs:
    """Tests for get_config_injection_args."""

    def test_returns_empty_for_none_path(self) -> None:
        """Should return empty list when no config path."""
        args = get_config_injection_args(
            tool_name="ruff",
            config_path=None,
        )

        assert args == []

    def test_ruff_args(self, tmp_path: Path) -> None:
        """Should return --config for Ruff.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.toml"

        args = get_config_injection_args(
            tool_name="ruff",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_black_args(self, tmp_path: Path) -> None:
        """Should return --config for Black.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.toml"

        args = get_config_injection_args(
            tool_name="black",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_prettier_args(self, tmp_path: Path) -> None:
        """Should return --config for Prettier.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.json"

        args = get_config_injection_args(
            tool_name="prettier",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_yamllint_args(self, tmp_path: Path) -> None:
        """Should return -c for yamllint.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.yaml"

        args = get_config_injection_args(
            tool_name="yamllint",
            config_path=config_path,
        )

        assert args == ["-c", str(config_path)]

    def test_bandit_args(self, tmp_path: Path) -> None:
        """Should return -c for Bandit.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.yaml"

        args = get_config_injection_args(
            tool_name="bandit",
            config_path=config_path,
        )

        assert args == ["-c", str(config_path)]


class TestGetNoAutoConfigArgs:
    """Tests for get_no_auto_config_args."""

    def test_ruff_isolated(self) -> None:
        """Should return --isolated for Ruff."""
        args = get_no_auto_config_args(tool_name="ruff")

        assert args == ["--isolated"]

    def test_prettier_no_args(self) -> None:
        """Prettier doesn't use --no-config (conflicts with --config)."""
        args = get_no_auto_config_args(tool_name="prettier")

        # Prettier errors if both --no-config and --config are passed
        assert args == []

    def test_black_no_args(self) -> None:
        """Black doesn't have no-auto-config flag."""
        args = get_no_auto_config_args(tool_name="black")

        assert args == []

    def test_unknown_tool(self) -> None:
        """Unknown tools should return empty list."""
        args = get_no_auto_config_args(tool_name="unknown")

        assert args == []


class TestGenerateToolConfig:
    """Tests for generate_tool_config."""

    def test_generates_config_file(self) -> None:
        """Should generate a temp config file."""
        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=100),
            tools={
                "prettier": ToolConfig(
                    settings={"singleQuote": True},
                ),
            },
        )

        config_path = generate_tool_config(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        assert config_path is not None
        assert config_path.exists()
        assert config_path.suffix == ".json"

        # Verify content
        content = json.loads(config_path.read_text())
        assert content["printWidth"] == 100
        assert content["singleQuote"] is True

        # Cleanup
        cleanup_temp_config(config_path)

    def test_returns_none_for_empty_config(self) -> None:
        """Should return None when no config to generate."""
        lintro_config = LintroConfig()

        config_path = generate_tool_config(
            tool_name="ruff",
            lintro_config=lintro_config,
        )

        assert config_path is None

    def test_loads_config_source(self, tmp_path: Path) -> None:
        """Should load config_source as base.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        # Create a native config file
        native_config = tmp_path / ".prettierrc"
        native_config.write_text('{"singleQuote": true, "tabWidth": 4}')

        lintro_config = LintroConfig(
            global_config=GlobalConfig(line_length=100),
            tools={
                "prettier": ToolConfig(
                    config_source=str(native_config),
                    overrides={"tabWidth": 2},  # Override tabWidth
                ),
            },
        )

        config_path = generate_tool_config(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        assert config_path is not None

        content = json.loads(config_path.read_text())
        # From native config
        assert content["singleQuote"] is True
        # From override (overrides native)
        assert content["tabWidth"] == 2
        # From global settings
        assert content["printWidth"] == 100

        cleanup_temp_config(config_path)


class TestCleanupTempConfig:
    """Tests for cleanup_temp_config."""

    def test_removes_file(self, tmp_path: Path) -> None:
        """Should remove the temp file.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_file = tmp_path / "test-config.json"
        config_file.write_text("{}")

        cleanup_temp_config(config_file)

        assert not config_file.exists()

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Should not raise for missing file.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_file = tmp_path / "nonexistent.json"

        # Should not raise
        cleanup_temp_config(config_file)
