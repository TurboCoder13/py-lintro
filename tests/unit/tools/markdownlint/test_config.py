"""Tests for _create_temp_markdownlint_config method."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_create_temp_config_creates_file(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Create temporary config file with correct structure.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    temp_path = markdownlint_plugin._create_temp_markdownlint_config(line_length=120)

    try:
        assert_that(temp_path).is_not_none()
        # temp_path is verified non-None by assertpy above
        assert_that(os.path.exists(temp_path)).is_true()  # type: ignore[arg-type]

        with open(temp_path, encoding="utf-8") as f:  # type: ignore[arg-type]
            config = json.load(f)

        assert_that(config).contains_key("config")
        assert_that(config["config"]).contains_key("MD013")
        assert_that(config["config"]["MD013"]["line_length"]).is_equal_to(120)
        assert_that(config["config"]["MD013"]["code_blocks"]).is_false()
        assert_that(config["config"]["MD013"]["tables"]).is_false()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def test_create_temp_config_handles_permission_error(
    markdownlint_plugin: MarkdownlintPlugin,
) -> None:
    """Handle permission error when creating temp config.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
    """
    with patch("tempfile.NamedTemporaryFile", side_effect=PermissionError("No write")):
        result = markdownlint_plugin._create_temp_markdownlint_config(line_length=80)
        assert_that(result).is_none()
