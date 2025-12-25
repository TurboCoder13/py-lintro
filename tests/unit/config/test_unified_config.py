"""Tests for the unified configuration manager."""

from __future__ import annotations

from assertpy import assert_that

from lintro.utils.unified_config import (
    DEFAULT_TOOL_PRIORITIES,
    GLOBAL_SETTINGS,
    ToolConfigInfo,
    ToolOrderStrategy,
    is_tool_injectable,
)


def test_has_priority_strategy() -> None:
    """Verify priority strategy exists."""
    assert_that(ToolOrderStrategy.PRIORITY).is_not_none()


def test_has_custom_strategy() -> None:
    """Verify custom strategy exists."""
    assert_that(ToolOrderStrategy.CUSTOM).is_not_none()


def test_default_values() -> None:
    """Verify default values are set correctly."""
    info = ToolConfigInfo(tool_name="ruff")

    assert_that(info.tool_name).is_equal_to("ruff")
    assert_that(info.native_config).is_equal_to({})
    assert_that(info.lintro_tool_config).is_equal_to({})
    assert_that(info.effective_config).is_equal_to({})
    assert_that(info.warnings).is_equal_to([])
    assert_that(info.is_injectable).is_true()


def test_line_length_setting_exists() -> None:
    """Verify line_length setting is defined."""
    assert_that(GLOBAL_SETTINGS).contains("line_length")


def test_line_length_has_tools() -> None:
    """Verify line_length has tool mappings."""
    assert_that(GLOBAL_SETTINGS["line_length"]).contains("tools")
    tools = GLOBAL_SETTINGS["line_length"]["tools"]

    assert_that(
        tools,
    ).contains("ruff")
    assert_that(
        tools,
    ).contains("black")
    assert_that(tools).contains("markdownlint")
    assert_that(tools).contains("prettier")
    assert_that(tools).contains("yamllint")

    def test_line_length_has_injectable_tools(self) -> None:
        """Verify injectable tools are defined.

        Args:
            self: Test instance.
        """
        assert_that(GLOBAL_SETTINGS["line_length"]).contains("injectable")
        injectable = GLOBAL_SETTINGS["line_length"]["injectable"]

        assert_that(injectable).contains("ruff")
        assert_that(injectable).contains("black")
        assert_that(injectable).contains("markdownlint")
        # Prettier and yamllint are now injectable via Lintro config generation
        assert_that(injectable).contains("prettier")
        assert_that(injectable).contains("yamllint")


class TestDefaultToolPriorities:
    """Tests for DEFAULT_TOOL_PRIORITIES."""

    def test_formatters_have_lower_priority(self) -> None:
        """Formatters should run before linters (lower priority value)."""
        assert DEFAULT_TOOL_PRIORITIES["prettier"] < DEFAULT_TOOL_PRIORITIES["ruff"]
        assert (
            DEFAULT_TOOL_PRIORITIES["black"] < DEFAULT_TOOL_PRIORITIES["markdownlint"]
        )

    def test_pytest_runs_last(self) -> None:
        """Pytest should have highest priority value (runs last)."""
        pytest_priority = DEFAULT_TOOL_PRIORITIES["pytest"]
        for tool, priority in DEFAULT_TOOL_PRIORITIES.items():
            if tool != "pytest":
                assert priority < pytest_priority


def test_ruff_is_injectable() -> None:
    """Ruff supports config injection."""
    assert is_tool_injectable("ruff") is True


def test_markdownlint_is_injectable() -> None:
    """Markdownlint supports config injection."""
    assert is_tool_injectable("markdownlint") is True


def test_yamllint_is_injectable() -> None:
    """Yamllint supports config injection via Lintro config generation."""
    assert is_tool_injectable("yamllint") is True
