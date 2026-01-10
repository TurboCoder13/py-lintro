"""Tests for YamllintPlugin.set_options method."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.enums.yamllint_format import YamllintFormat

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


# Tests for valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("format", "parsable"),
        ("format", "standard"),
        ("format", "colored"),
        ("format", "github"),
        ("format", "auto"),
        ("config_file", "/path/to/config.yml"),
        ("config_data", "extends: default"),
        ("strict", True),
        ("strict", False),
        ("relaxed", True),
        ("relaxed", False),
        ("no_warnings", True),
        ("no_warnings", False),
    ],
    ids=[
        "format_parsable",
        "format_standard",
        "format_colored",
        "format_github",
        "format_auto",
        "config_file_path",
        "config_data_yaml",
        "strict_true",
        "strict_false",
        "relaxed_true",
        "relaxed_false",
        "no_warnings_true",
        "no_warnings_false",
    ],
)
def test_set_options_valid(
    yamllint_plugin: YamllintPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
    """
    yamllint_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(yamllint_plugin.options.get(option_name)).is_equal_to(option_value)


# Tests for invalid option types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("config_file", 123, "config_file must be a string"),
        ("config_file", True, "config_file must be a string"),
        ("config_data", 123, "config_data must be a string"),
        ("config_data", True, "config_data must be a string"),
        ("strict", "yes", "strict must be a boolean"),
        ("strict", 1, "strict must be a boolean"),
        ("relaxed", "yes", "relaxed must be a boolean"),
        ("relaxed", 1, "relaxed must be a boolean"),
        ("no_warnings", "yes", "no_warnings must be a boolean"),
        ("no_warnings", 1, "no_warnings must be a boolean"),
    ],
    ids=[
        "invalid_config_file_int",
        "invalid_config_file_bool",
        "invalid_config_data_int",
        "invalid_config_data_bool",
        "invalid_strict_string",
        "invalid_strict_int",
        "invalid_relaxed_string",
        "invalid_relaxed_int",
        "invalid_no_warnings_string",
        "invalid_no_warnings_int",
    ],
)
def test_set_options_invalid_type(
    yamllint_plugin: YamllintPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
        option_name: Name of the option being tested.
        invalid_value: Invalid value that should cause an error.
        error_match: Expected error message substring.
    """
    with pytest.raises(ValueError, match=error_match):
        yamllint_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


def test_set_options_invalid_format_defaults_to_parsable(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Invalid format defaults to parsable (normalize_yamllint_format behavior).

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    yamllint_plugin.set_options(format="invalid_format")
    # normalize_yamllint_format defaults to PARSABLE for unrecognized formats
    assert_that(yamllint_plugin.options["format"]).is_equal_to("parsable")


def test_set_options_with_enum_format(yamllint_plugin: YamllintPlugin) -> None:
    """Set options accepts YamllintFormat enum.

    Args:
        yamllint_plugin: The yamllint plugin instance to test.
    """
    yamllint_plugin.set_options(format=YamllintFormat.GITHUB)
    assert_that(yamllint_plugin.options.get("format")).is_equal_to("github")
