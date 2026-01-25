"""Tests for pydoclint plugin set_options method."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.enums.pydoclint_style import PydoclintStyle
from lintro.tools.definitions.pydoclint import PydoclintPlugin


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("style", "google"),
        ("style", "numpy"),
        ("style", "sphinx"),
        ("check_return_types", True),
        ("check_return_types", False),
        ("check_arg_order", True),
        ("check_arg_order", False),
        ("skip_checking_short_docstrings", True),
        ("skip_checking_short_docstrings", False),
        ("quiet", True),
        ("quiet", False),
    ],
    ids=[
        "style_google",
        "style_numpy",
        "style_sphinx",
        "check_return_types_true",
        "check_return_types_false",
        "check_arg_order_true",
        "check_arg_order_false",
        "skip_checking_short_docstrings_true",
        "skip_checking_short_docstrings_false",
        "quiet_true",
        "quiet_false",
    ],
)
def test_set_options_valid(
    pydoclint_plugin: PydoclintPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    pydoclint_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(pydoclint_plugin.options.get(option_name)).is_equal_to(option_value)


def test_set_options_style_enum(pydoclint_plugin: PydoclintPlugin) -> None:
    """Set style option with enum value.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(style=PydoclintStyle.NUMPY)
    assert_that(pydoclint_plugin.options.get("style")).is_equal_to("numpy")


def test_set_options_invalid_style_defaults_to_google(
    pydoclint_plugin: PydoclintPlugin,
) -> None:
    """Invalid style value defaults to google.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(style="invalid_style")
    assert_that(pydoclint_plugin.options.get("style")).is_equal_to("google")


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("check_return_types", "yes", "check_return_types must be a boolean"),
        ("check_arg_order", "yes", "check_arg_order must be a boolean"),
        (
            "skip_checking_short_docstrings",
            "yes",
            "skip_checking_short_docstrings must be a boolean",
        ),
        ("quiet", "yes", "quiet must be a boolean"),
    ],
    ids=[
        "invalid_check_return_types_type",
        "invalid_check_arg_order_type",
        "invalid_skip_checking_short_docstrings_type",
        "invalid_quiet_type",
    ],
)
def test_set_options_invalid_type(
    pydoclint_plugin: PydoclintPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        pydoclint_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]
