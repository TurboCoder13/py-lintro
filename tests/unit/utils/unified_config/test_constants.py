"""Tests for GLOBAL_SETTINGS and DEFAULT_TOOL_PRIORITIES constants."""

from __future__ import annotations

from assertpy import assert_that

from lintro.utils.unified_config import DEFAULT_TOOL_PRIORITIES, GLOBAL_SETTINGS

# Tests for GLOBAL_SETTINGS constant


def test_global_settings_line_length_has_expected_tools() -> None:
    """Verify line_length setting includes expected tools."""
    tools = GLOBAL_SETTINGS["line_length"]["tools"]

    assert_that(tools).contains_key("ruff")
    assert_that(tools).contains_key("black")
    assert_that(tools).contains_key("prettier")
    assert_that(tools).contains_key("markdownlint")
    assert_that(tools).contains_key("yamllint")


def test_global_settings_line_length_has_injectable_tools() -> None:
    """Verify line_length has a set of injectable tools."""
    injectable = GLOBAL_SETTINGS["line_length"]["injectable"]

    assert_that(injectable).contains("ruff")
    assert_that(injectable).contains("black")
    assert_that(injectable).contains("prettier")


def test_global_settings_has_multiple_settings() -> None:
    """Verify GLOBAL_SETTINGS includes multiple setting types."""
    assert_that(GLOBAL_SETTINGS).contains_key("line_length")
    assert_that(GLOBAL_SETTINGS).contains_key("target_python")
    assert_that(GLOBAL_SETTINGS).contains_key("indent_size")


# Tests for DEFAULT_TOOL_PRIORITIES constant


def test_default_tool_priorities_formatters_before_linters() -> None:
    """Verify formatters have lower priority (run first) than linters."""
    assert_that(DEFAULT_TOOL_PRIORITIES["prettier"]).is_less_than(
        DEFAULT_TOOL_PRIORITIES["bandit"],
    )
    assert_that(DEFAULT_TOOL_PRIORITIES["black"]).is_less_than(
        DEFAULT_TOOL_PRIORITIES["darglint"],
    )
    assert_that(DEFAULT_TOOL_PRIORITIES["ruff"]).is_less_than(
        DEFAULT_TOOL_PRIORITIES["bandit"],
    )


def test_default_tool_priorities_pytest_runs_last() -> None:
    """Verify pytest has highest priority (runs last)."""
    pytest_priority = DEFAULT_TOOL_PRIORITIES["pytest"]

    for tool, priority in DEFAULT_TOOL_PRIORITIES.items():
        if tool != "pytest":
            assert_that(priority).is_less_than(pytest_priority)


def test_default_tool_priorities_has_expected_tools() -> None:
    """Verify DEFAULT_TOOL_PRIORITIES includes expected tools."""
    expected_tools = [
        "prettier",
        "black",
        "ruff",
        "markdownlint",
        "yamllint",
        "bandit",
        "pytest",
    ]

    for tool in expected_tools:
        assert_that(DEFAULT_TOOL_PRIORITIES).contains_key(tool)
