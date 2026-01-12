"""Tests for ToolOptionsSpec in lintro.tools.core.option_spec module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.tools.core.option_spec import (
    OptionSpec,
    OptionType,
    ToolOptionsSpec,
    bool_option,
    int_option,
    str_option,
)


def test_add_returns_self_for_chaining() -> None:
    """Add method returns self for method chaining."""
    spec = ToolOptionsSpec()
    result = spec.add(bool_option("preview", "--preview"))
    assert_that(result).is_same_as(spec)


def test_add_multiple_options_via_chaining() -> None:
    """Multiple options can be added via chaining."""
    spec = (
        ToolOptionsSpec()
        .add(bool_option("preview", "--preview"))
        .add(int_option("line_length", "--line-length", default=88))
        .add(str_option("target", "--target"))
    )
    assert_that(spec.options).contains_key("preview", "line_length", "target")


def test_validate_all_valid_values() -> None:
    """Validate all passes for valid values."""
    spec = (
        ToolOptionsSpec()
        .add(bool_option("preview", "--preview"))
        .add(int_option("line_length", "--line-length"))
    )
    # Should not raise - if it does, test fails
    spec.validate_all({"preview": True, "line_length": 88})
    # Explicit pass indicator
    assert_that(True).is_true()


def test_validate_all_rejects_invalid_value() -> None:
    """Validate all raises for invalid value."""
    spec = ToolOptionsSpec().add(
        int_option("line_length", "--line-length", min_value=1),
    )
    with pytest.raises(ValueError, match="line_length"):
        spec.validate_all({"line_length": 0})


def test_validate_all_checks_required() -> None:
    """Validate all checks required options."""
    spec = ToolOptionsSpec().add(
        OptionSpec(
            name="required_opt",
            cli_flag="--required",
            option_type=OptionType.STR,
            required=True,
        ),
    )
    with pytest.raises(ValueError, match="required_opt is required"):
        spec.validate_all({})


def test_to_cli_args() -> None:
    """Convert all values to CLI args."""
    spec = (
        ToolOptionsSpec()
        .add(bool_option("preview", "--preview"))
        .add(int_option("line_length", "--line-length"))
    )
    result = spec.to_cli_args({"preview": True, "line_length": 88})
    assert_that(result).contains("--preview", "--line-length", "88")


def test_to_cli_args_skips_false_bools() -> None:
    """CLI args skips False boolean values."""
    spec = ToolOptionsSpec().add(bool_option("preview", "--preview"))
    result = spec.to_cli_args({"preview": False})
    assert_that(result).is_empty()


def test_get_defaults() -> None:
    """Get defaults returns default values."""
    spec = (
        ToolOptionsSpec()
        .add(bool_option("preview", "--preview", default=False))
        .add(int_option("line_length", "--line-length", default=88))
        .add(str_option("target", "--target"))
    )
    defaults = spec.get_defaults()
    assert_that(defaults).is_equal_to({"preview": False, "line_length": 88})


def test_get_defaults_empty_when_no_defaults() -> None:
    """Get defaults returns empty dict when no defaults."""
    spec = (
        ToolOptionsSpec()
        .add(bool_option("preview", "--preview"))
        .add(str_option("target", "--target"))
    )
    assert_that(spec.get_defaults()).is_empty()
