"""Tests for LintroConfig dataclasses."""

from lintro.config.lintro_config import (
    ExecutionConfig,
    GlobalConfig,
    LintroConfig,
    ToolConfig,
)


class TestGlobalConfig:
    """Tests for GlobalConfig dataclass."""

    def test_default_values(self) -> None:
        """GlobalConfig should have None defaults."""
        config = GlobalConfig()

        assert config.line_length is None
        assert config.target_python is None
        assert config.indent_size is None
        assert config.quote_style is None

    def test_with_values(self) -> None:
        """GlobalConfig should accept all values."""
        config = GlobalConfig(
            line_length=88,
            target_python="py313",
            indent_size=4,
            quote_style="double",
        )

        assert config.line_length == 88
        assert config.target_python == "py313"
        assert config.indent_size == 4
        assert config.quote_style == "double"


class TestExecutionConfig:
    """Tests for ExecutionConfig dataclass."""

    def test_default_values(self) -> None:
        """ExecutionConfig should have sensible defaults."""
        config = ExecutionConfig()

        assert config.enabled_tools == []
        assert config.tool_order == "priority"
        assert config.fail_fast is False
        assert config.parallel is False

    def test_with_custom_order(self) -> None:
        """ExecutionConfig should accept custom tool order."""
        config = ExecutionConfig(
            enabled_tools=["ruff", "prettier"],
            tool_order=["prettier", "ruff"],
            fail_fast=True,
        )

        assert config.enabled_tools == ["ruff", "prettier"]
        assert config.tool_order == ["prettier", "ruff"]
        assert config.fail_fast is True


class TestToolConfig:
    """Tests for ToolConfig dataclass."""

    def test_default_values(self) -> None:
        """ToolConfig should have sensible defaults."""
        config = ToolConfig()

        assert config.enabled is True
        assert config.config_source is None
        assert config.overrides == {}
        assert config.settings == {}

    def test_with_config_source(self) -> None:
        """ToolConfig should accept config_source."""
        config = ToolConfig(
            enabled=True,
            config_source=".prettierrc",
            overrides={"printWidth": 88},
        )

        assert config.config_source == ".prettierrc"
        assert config.overrides["printWidth"] == 88

    def test_get_effective_settings(self) -> None:
        """get_effective_settings should merge settings and overrides."""
        config = ToolConfig(
            settings={"a": 1, "b": 2},
            overrides={"b": 3, "c": 4},
        )

        effective = config.get_effective_settings()

        assert effective == {"a": 1, "b": 3, "c": 4}


class TestLintroConfig:
    """Tests for LintroConfig dataclass."""

    def test_default_values(self) -> None:
        """LintroConfig should have sensible defaults."""
        config = LintroConfig()

        assert config.global_config is not None
        assert config.execution is not None
        assert config.tools == {}
        assert config.config_path is None

    def test_get_tool_config_returns_default(self) -> None:
        """get_tool_config should return default for unknown tools."""
        config = LintroConfig()

        tool_config = config.get_tool_config("unknown_tool")

        assert tool_config.enabled is True
        assert tool_config.config_source is None

    def test_get_tool_config_returns_configured(self) -> None:
        """get_tool_config should return configured tool config."""
        config = LintroConfig(
            tools={
                "ruff": ToolConfig(
                    enabled=False,
                    settings={"select": ["E", "F"]},
                ),
            },
        )

        tool_config = config.get_tool_config("ruff")

        assert tool_config.enabled is False
        assert tool_config.settings["select"] == ["E", "F"]

    def test_get_tool_config_case_insensitive(self) -> None:
        """get_tool_config should be case insensitive."""
        config = LintroConfig(
            tools={"ruff": ToolConfig(enabled=False)},
        )

        # Lowercase should work
        assert config.get_tool_config("ruff").enabled is False
        # Uppercase should also work (converted to lowercase)
        assert config.get_tool_config("RUFF").enabled is False
        # Mixed case should also work
        assert config.get_tool_config("Ruff").enabled is False

    def test_is_tool_enabled_all_tools(self) -> None:
        """is_tool_enabled should return True when enabled_tools is empty."""
        config = LintroConfig()

        assert config.is_tool_enabled("ruff") is True
        assert config.is_tool_enabled("prettier") is True

    def test_is_tool_enabled_filtered(self) -> None:
        """is_tool_enabled should filter by enabled_tools."""
        config = LintroConfig(
            execution=ExecutionConfig(enabled_tools=["ruff"]),
        )

        assert config.is_tool_enabled("ruff") is True
        assert config.is_tool_enabled("prettier") is False

    def test_is_tool_enabled_tool_disabled(self) -> None:
        """is_tool_enabled should respect tool-level enabled flag."""
        config = LintroConfig(
            tools={"ruff": ToolConfig(enabled=False)},
        )

        assert config.is_tool_enabled("ruff") is False

    def test_get_effective_line_length_from_global(self) -> None:
        """get_effective_line_length should use global setting."""
        config = LintroConfig(
            global_config=GlobalConfig(line_length=120),
        )

        assert config.get_effective_line_length("ruff") == 120

    def test_get_effective_line_length_from_tool_settings(self) -> None:
        """get_effective_line_length should prefer tool settings."""
        config = LintroConfig(
            global_config=GlobalConfig(line_length=120),
            tools={
                "ruff": ToolConfig(settings={"line_length": 88}),
            },
        )

        assert config.get_effective_line_length("ruff") == 88

    def test_get_effective_line_length_from_tool_overrides(self) -> None:
        """get_effective_line_length should prefer tool overrides."""
        config = LintroConfig(
            global_config=GlobalConfig(line_length=120),
            tools={
                "ruff": ToolConfig(
                    settings={"line_length": 88},
                    overrides={"line_length": 100},
                ),
            },
        )

        assert config.get_effective_line_length("ruff") == 100

    def test_get_effective_target_python(self) -> None:
        """get_effective_target_python should cascade properly."""
        config = LintroConfig(
            global_config=GlobalConfig(target_python="py312"),
        )

        assert config.get_effective_target_python("ruff") == "py312"

        # Tool override should win
        config.tools["ruff"] = ToolConfig(overrides={"target_python": "py313"})
        assert config.get_effective_target_python("ruff") == "py313"
