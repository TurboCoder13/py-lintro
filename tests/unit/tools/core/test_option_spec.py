"""Tests for OptionSpec validation in lintro.tools.core.option_spec module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.tools.core.option_spec import (
    OptionSpec,
    OptionType,
    bool_option,
    enum_option,
    int_option,
    list_option,
    positive_int_option,
    str_option,
)


def test_bool_option_validates_true() -> None:
    """Bool option accepts True value."""
    spec = bool_option("preview", "--preview")
    spec.validate(True)


def test_bool_option_validates_false() -> None:
    """Bool option accepts False value."""
    spec = bool_option("preview", "--preview")
    spec.validate(False)


def test_bool_option_rejects_non_bool() -> None:
    """Bool option rejects non-boolean values."""
    spec = bool_option("preview", "--preview")
    with pytest.raises(ValueError, match="preview"):
        spec.validate("not a bool")


def test_bool_option_to_cli_args_true() -> None:
    """Bool option converts True to CLI flag."""
    spec = bool_option("preview", "--preview")
    assert_that(spec.to_cli_args(True)).is_equal_to(["--preview"])


def test_bool_option_to_cli_args_false() -> None:
    """Bool option converts False to empty list."""
    spec = bool_option("preview", "--preview")
    assert_that(spec.to_cli_args(False)).is_equal_to([])


def test_int_option_validates_valid_int() -> None:
    """Int option accepts valid integer."""
    spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
    spec.validate(88)


def test_int_option_rejects_below_min() -> None:
    """Int option rejects value below minimum."""
    spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
    with pytest.raises(ValueError, match="line_length"):
        spec.validate(0)


def test_int_option_rejects_above_max() -> None:
    """Int option rejects value above maximum."""
    spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
    with pytest.raises(ValueError, match="line_length"):
        spec.validate(201)


def test_positive_int_option_rejects_zero() -> None:
    """Positive int option rejects zero."""
    spec = positive_int_option("timeout", "--timeout")
    with pytest.raises(ValueError, match="timeout"):
        spec.validate(0)


def test_str_option_with_choices_rejects_invalid() -> None:
    """Str option with choices rejects invalid choice."""
    spec = str_option("target", "--target", choices=["py38", "py311"])
    with pytest.raises(ValueError, match="target must be one of"):
        spec.validate("py37")


def test_list_option_rejects_non_list() -> None:
    """List option rejects non-list values."""
    spec = list_option("ignore", "--ignore")
    with pytest.raises(ValueError, match="ignore"):
        spec.validate("not a list")


def test_list_option_to_cli_args() -> None:
    """List option converts each item to CLI args."""
    spec = list_option("ignore", "--ignore")
    result = spec.to_cli_args(["E501", "W503"])
    assert_that(result).is_equal_to(["--ignore", "E501", "--ignore", "W503"])


def test_enum_option_rejects_invalid_choice() -> None:
    """Enum option rejects invalid choice."""
    spec = enum_option("severity", "--severity", choices=["error", "warning"])
    with pytest.raises(ValueError, match="severity must be one of"):
        spec.validate("info")


def test_required_option_validates_none() -> None:
    """Required option raises on None value."""
    spec = OptionSpec(
        name="required_opt",
        cli_flag="--required",
        option_type=OptionType.STR,
        required=True,
    )
    with pytest.raises(ValueError, match="required_opt is required"):
        spec.validate(None)


def test_optional_option_accepts_none() -> None:
    """Optional option accepts None value."""
    spec = str_option("optional", "--optional")
    spec.validate(None)
