"""Tests for config file list constants."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import (
    BIOME_CONFIG_FILES,
    MARKDOWNLINT_CONFIG_FILES,
    PRETTIER_CONFIG_FILES,
    YAMLLINT_CONFIG_FILES,
)


@pytest.mark.parametrize(
    ("config_list", "expected_files"),
    [
        (YAMLLINT_CONFIG_FILES, [".yamllint", ".yamllint.yaml", ".yamllint.yml"]),
        (PRETTIER_CONFIG_FILES, [".prettierrc", ".prettierrc.json"]),
        (BIOME_CONFIG_FILES, ["biome.json", "biome.jsonc"]),
        (
            MARKDOWNLINT_CONFIG_FILES,
            [
                ".markdownlint.json",
                ".markdownlint.yaml",
                ".markdownlint.yml",
                ".markdownlint.jsonc",
            ],
        ),
    ],
    ids=["yamllint_files", "prettier_files", "biome_files", "markdownlint_files"],
)
def test_config_file_lists_contain_expected_files(
    config_list: tuple[str, ...],
    expected_files: list[str],
) -> None:
    """Verify config file list constants contain all expected filenames.

    Args:
        config_list: The config file list constant to check.
        expected_files: List of filenames expected to be in the constant.
    """
    for expected_file in expected_files:
        assert_that(config_list).contains(expected_file)
