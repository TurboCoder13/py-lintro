"""Tests for BiomePlugin default options."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.tools.definitions.biome import BIOME_DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from lintro.tools.definitions.biome import BiomePlugin


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", BIOME_DEFAULT_TIMEOUT),
        ("use_vcs_ignore", True),
        ("verbose_fix_output", False),
    ],
    ids=[
        "timeout_equals_default",
        "use_vcs_ignore_is_true",
        "verbose_fix_output_is_false",
    ],
)
def test_default_options_values(
    biome_plugin: BiomePlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        biome_plugin: The BiomePlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(biome_plugin.definition.default_options).contains_key(option_name)
    assert_that(biome_plugin.definition.default_options[option_name]).is_equal_to(
        expected_value,
    )
