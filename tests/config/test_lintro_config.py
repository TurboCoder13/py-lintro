"""Tests for LintroConfig dataclasses."""

from lintro.config.lintro_config import (
    EnforceConfig,
    ExecutionConfig,
    GlobalConfig,
    LintroConfig,
    ToolConfig,
)


class TestEnforceConfig:
    """Tests for EnforceConfig dataclass."""

    def test_default_values(self) -> None:
        """EnforceConfig should have None defaults."""
        config = EnforceConfig()

        assert config.line_length is None
        assert config.target_python is None

    def test_with_values(self) -> None:
        """EnforceConfig should accept all values."""
        config = EnforceConfig(
            line_length=88,
            target_python="py313",
        )

        assert config.line_length == 88
        assert config.target_python == "py313"


class TestGlobalConfigAlias:
    """Tests for GlobalConfig alias (backward compatibility)."""

    def test_global_config_is_enforce_config(self) -> None:
        """GlobalConfig should be an alias for EnforceConfig."""
        assert GlobalConfig is EnforceConfig

    def test_global_config_default_values(self) -> None:
        """GlobalConfig should have None defaults."""
        config = GlobalConfig()

        assert config.line_length is None
        assert config.target_python is None


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

    def test_with_config_source(self) -> None:
        """ToolConfig should accept config_source."""
        config = ToolConfig(
            enabled=True,
            config_source=".prettierrc",
        )

        assert config.config_source == ".prettierrc"


class TestLintroConfig:
    """Tests for LintroConfig dataclass."""

    def test_default_values(self) -> None:
        """LintroConfig should have sensible defaults."""
        config = LintroConfig()

        assert config.enforce is not None
        assert config.execution is not None
        assert config.defaults == {}
        assert config.tools == {}
        assert config.config_path is None

    def test_global_config_property(self) -> None:
        """global_config property should return enforce config."""
        config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
        )

        assert config.global_config is config.enforce
        assert config.global_config.line_length == 88

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
                "ruff": ToolConfig(enabled=False),
            },
        )

        tool_config = config.get_tool_config("ruff")

        assert tool_config.enabled is False

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

    def test_get_tool_defaults(self) -> None:
        """get_tool_defaults should return defaults for a tool."""
        config = LintroConfig(
            defaults={
                "prettier": {"singleQuote": True, "tabWidth": 2},
            },
        )

        defaults = config.get_tool_defaults("prettier")

        assert defaults["singleQuote"] is True
        assert defaults["tabWidth"] == 2

    def test_get_tool_defaults_empty(self) -> None:
        """get_tool_defaults should return empty dict for unknown tools."""
        config = LintroConfig()

        defaults = config.get_tool_defaults("unknown")

        assert defaults == {}

    def test_get_effective_line_length_from_enforce(self) -> None:
        """get_effective_line_length should use enforce setting."""
        config = LintroConfig(
            enforce=EnforceConfig(line_length=120),
        )

        assert config.get_effective_line_length("ruff") == 120
        assert config.get_effective_line_length("prettier") == 120

    def test_get_effective_line_length_returns_none(self) -> None:
        """get_effective_line_length should return None when not set."""
        config = LintroConfig()

        assert config.get_effective_line_length("ruff") is None

    def test_get_effective_target_python(self) -> None:
        """get_effective_target_python should use enforce setting."""
        config = LintroConfig(
            enforce=EnforceConfig(target_python="py312"),
        )

        assert config.get_effective_target_python("ruff") == "py312"
        assert config.get_effective_target_python("black") == "py312"

    def test_get_effective_target_python_returns_none(self) -> None:
        """get_effective_target_python should return None when not set."""
        config = LintroConfig()

        assert config.get_effective_target_python("ruff") is None
        assert config.get_effective_target_python("black") is None
