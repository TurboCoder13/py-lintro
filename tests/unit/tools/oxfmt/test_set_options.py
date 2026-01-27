"""Tests for OxfmtPlugin.set_options() method."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.oxfmt import OxfmtPlugin


# =============================================================================
# Tests for config and ignore_path options validation
# =============================================================================


def test_config_accepts_string(oxfmt_plugin: OxfmtPlugin) -> None:
    """Config option accepts a string value.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(config=".oxfmtrc.custom.json")
    assert_that(oxfmt_plugin.options.get("config")).is_equal_to(
        ".oxfmtrc.custom.json",
    )


def test_config_rejects_non_string(oxfmt_plugin: OxfmtPlugin) -> None:
    """Config option rejects non-string values.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="config must be a string"):
        # Intentionally passing wrong type to test validation
        oxfmt_plugin.set_options(config=123)  # type: ignore[arg-type]


def test_ignore_path_accepts_string(oxfmt_plugin: OxfmtPlugin) -> None:
    """Ignore_path option accepts a string value.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(ignore_path=".oxfmtignore")
    assert_that(oxfmt_plugin.options.get("ignore_path")).is_equal_to(
        ".oxfmtignore",
    )


def test_ignore_path_rejects_non_string(oxfmt_plugin: OxfmtPlugin) -> None:
    """Ignore_path option rejects non-string values.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="ignore_path must be a string"):
        # Intentionally passing wrong type to test validation
        oxfmt_plugin.set_options(ignore_path=True)  # type: ignore[arg-type]


# =============================================================================
# Tests for formatting options validation
# =============================================================================


@pytest.mark.parametrize(
    ("option_name", "value", "expected"),
    [
        ("print_width", 120, 120),
        ("tab_width", 4, 4),
        ("use_tabs", True, True),
        ("use_tabs", False, False),
        ("semi", True, True),
        ("semi", False, False),
        ("single_quote", True, True),
        ("single_quote", False, False),
    ],
    ids=[
        "print_width_accepts_integer",
        "tab_width_accepts_integer",
        "use_tabs_accepts_true",
        "use_tabs_accepts_false",
        "semi_accepts_true",
        "semi_accepts_false",
        "single_quote_accepts_true",
        "single_quote_accepts_false",
    ],
)
def test_formatting_option_accepts_valid_input(
    oxfmt_plugin: OxfmtPlugin,
    option_name: str,
    value: int | bool,
    expected: int | bool,
) -> None:
    """Formatting options accept valid values.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
        option_name: The name of the option to set.
        value: The value to set.
        expected: The expected value.
    """
    # Mypy can't infer types from parametrized kwargs
    oxfmt_plugin.set_options(**{option_name: value})  # type: ignore[arg-type]
    assert_that(oxfmt_plugin.options.get(option_name)).is_equal_to(expected)


def test_print_width_rejects_non_integer(oxfmt_plugin: OxfmtPlugin) -> None:
    """Print_width option rejects non-integer values.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="print_width must be an integer"):
        # Intentionally passing wrong type to test validation
        oxfmt_plugin.set_options(print_width="120")  # type: ignore[arg-type]


def test_print_width_rejects_zero(oxfmt_plugin: OxfmtPlugin) -> None:
    """Print_width option rejects zero.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="print_width must be at least 1"):
        oxfmt_plugin.set_options(print_width=0)


def test_tab_width_rejects_zero(oxfmt_plugin: OxfmtPlugin) -> None:
    """Tab_width option rejects zero.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="tab_width must be at least 1"):
        oxfmt_plugin.set_options(tab_width=0)


def test_use_tabs_rejects_non_boolean(oxfmt_plugin: OxfmtPlugin) -> None:
    """Use_tabs option rejects non-boolean values.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    with pytest.raises(ValueError, match="use_tabs must be a boolean"):
        # Intentionally passing wrong type to test validation
        oxfmt_plugin.set_options(use_tabs="true")  # type: ignore[arg-type]


# =============================================================================
# Tests for setting multiple options
# =============================================================================


def test_set_multiple_options(oxfmt_plugin: OxfmtPlugin) -> None:
    """Multiple options can be set in a single call.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(
        config=".oxfmtrc.json",
        print_width=100,
        tab_width=4,
        use_tabs=False,
        semi=True,
        single_quote=True,
    )

    assert_that(oxfmt_plugin.options.get("config")).is_equal_to(".oxfmtrc.json")
    assert_that(oxfmt_plugin.options.get("print_width")).is_equal_to(100)
    assert_that(oxfmt_plugin.options.get("tab_width")).is_equal_to(4)
    assert_that(oxfmt_plugin.options.get("use_tabs")).is_false()
    assert_that(oxfmt_plugin.options.get("semi")).is_true()
    assert_that(oxfmt_plugin.options.get("single_quote")).is_true()


# =============================================================================
# Tests for _build_oxfmt_args(oxfmt_plugin.options) helper method
# =============================================================================


def test_build_args_empty_options(oxfmt_plugin: OxfmtPlugin) -> None:
    """Empty options returns empty args list.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).is_empty()


def test_build_args_config_adds_flag(oxfmt_plugin: OxfmtPlugin) -> None:
    """Config option adds --config flag.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(config=".oxfmtrc.json")
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).contains("--config", ".oxfmtrc.json")


def test_build_args_ignore_path_adds_flag(oxfmt_plugin: OxfmtPlugin) -> None:
    """Ignore_path option adds --ignore-path flag.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(ignore_path=".oxfmtignore")
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).contains("--ignore-path", ".oxfmtignore")


def test_build_args_print_width_adds_flag(oxfmt_plugin: OxfmtPlugin) -> None:
    """Print_width option adds --print-width flag.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(print_width=120)
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).contains("--print-width", "120")


def test_build_args_tab_width_adds_flag(oxfmt_plugin: OxfmtPlugin) -> None:
    """Tab_width option adds --tab-width flag.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(tab_width=4)
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).contains("--tab-width", "4")


@pytest.mark.parametrize(
    ("option_name", "value", "expected_flag"),
    [
        ("use_tabs", True, "--use-tabs"),
        ("use_tabs", False, "--no-use-tabs"),
        ("semi", True, "--semi"),
        ("semi", False, "--no-semi"),
        ("single_quote", True, "--single-quote"),
        ("single_quote", False, "--no-single-quote"),
    ],
    ids=[
        "use_tabs_true",
        "use_tabs_false",
        "semi_true",
        "semi_false",
        "single_quote_true",
        "single_quote_false",
    ],
)
def test_build_args_boolean_options_add_flags(
    oxfmt_plugin: OxfmtPlugin,
    option_name: str,
    value: bool,
    expected_flag: str,
) -> None:
    """Boolean options add correct flags.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
        option_name: The option name to set.
        value: The boolean value to set.
        expected_flag: The expected CLI flag.
    """
    # Mypy can't infer types from parametrized kwargs
    oxfmt_plugin.set_options(**{option_name: value})  # type: ignore[arg-type]
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)
    assert_that(args).contains(expected_flag)


def test_build_args_multiple_options_combine(oxfmt_plugin: OxfmtPlugin) -> None:
    """Multiple options combine into a single args list.

    Args:
        oxfmt_plugin: The OxfmtPlugin instance to test.
    """
    oxfmt_plugin.set_options(
        config=".oxfmtrc.json",
        print_width=100,
        semi=False,
        single_quote=True,
    )
    args = oxfmt_plugin._build_oxfmt_args(oxfmt_plugin.options)

    assert_that(args).contains("--config", ".oxfmtrc.json")
    assert_that(args).contains("--print-width", "100")
    assert_that(args).contains("--no-semi")
    assert_that(args).contains("--single-quote")
