"""Tests for LintroConfig dataclasses."""

from assertpy import assert_that

from lintro.config.lintro_config import (
    EnforceConfig,
    ExecutionConfig,
    LintroConfig,
    ToolConfig,
)


def test_default_values() -> None:
    """EnforceConfig should have None defaults."""
    config = EnforceConfig()

    assert config.line_length is None
    assert config.target_python is None


def test_execution_config_defaults() -> None:
    """ExecutionConfig should have sensible defaults."""
    config = ExecutionConfig()

    assert_that(config.enabled_tools).is_equal_to([])
    assert_that(config.tool_order).is_equal_to("priority")
    assert config.fail_fast is False
    assert config.parallel is False


def test_tool_config_defaults() -> None:
    """ToolConfig should have sensible defaults."""
    config = ToolConfig()

    assert config.enabled is True
    assert config.config_source is None


def test_lintro_config_defaults() -> None:
    """LintroConfig should have sensible defaults."""
    config = LintroConfig()

    assert config.enforce is not None
    assert config.execution is not None
    assert_that(config.defaults).is_equal_to({})
    assert_that(config.tools).is_equal_to({})
    assert config.config_path is None


def test_get_tool_config_returns_default() -> None:
    """get_tool_config should return default for unknown tools."""
    config = LintroConfig()

    tool_config = config.get_tool_config("unknown_tool")

    assert tool_config.enabled is True
    assert tool_config.config_source is None


def test_get_tool_config_case_insensitive() -> None:
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


def test_is_tool_enabled_filtered() -> None:
    """is_tool_enabled should filter by enabled_tools."""
    config = LintroConfig(
        execution=ExecutionConfig(enabled_tools=["ruff"]),
    )

    assert config.is_tool_enabled("ruff") is True
    assert config.is_tool_enabled("prettier") is False


def test_get_tool_defaults() -> None:
    """get_tool_defaults should return defaults for a tool."""
    config = LintroConfig(
        defaults={
            "prettier": {"singleQuote": True, "tabWidth": 2},
        },
    )

    defaults = config.get_tool_defaults("prettier")

    assert defaults["singleQuote"] is True
    assert defaults["tabWidth"] == 2


def test_get_effective_line_length_from_enforce() -> None:
    """get_effective_line_length should use enforce setting."""
    config = LintroConfig(
        enforce=EnforceConfig(line_length=120),
    )

    assert config.get_effective_line_length("ruff") == 120
    assert config.get_effective_line_length("prettier") == 120


def test_get_effective_target_python() -> None:
    """get_effective_target_python should use enforce setting."""
    config = LintroConfig(
        enforce=EnforceConfig(target_python="py312"),
    )

    assert config.get_effective_target_python("ruff") == "py312"
    assert config.get_effective_target_python("black") == "py312"
