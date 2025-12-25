"""Unit tests for BaseTool configuration methods.

Tests the tiered configuration model:
1. _get_enforce_cli_args() - CLI flag injection for enforce settings
2. _get_defaults_config_args() - Defaults config injection
3. _build_config_args() - Combined config args
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Never

import pytest
from assertpy import assert_that

from lintro.config.config_loader import clear_config_cache
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.tools.core.tool_base import BaseTool


class _DummyTool(BaseTool):
    """Dummy tool for testing config injection."""

    name: str = "ruff"  # Use ruff since it has enforce mappings
    description: str = "dummy ruff for testing"
    can_fix: bool = False
    config: ToolConfig = ToolConfig(
        priority=1,
        conflicts_with=[],
        file_patterns=["*.py"],
        tool_type=ToolType.LINTER,
    )

    def check(self, paths: list[str]) -> Never:
        """Check files (not implemented for tests).

        Args:
            paths: List of paths to check.

        Raises:
            NotImplementedError: Always raised for dummy tool.
        """
        raise NotImplementedError

    def fix(self, paths: list[str]) -> Never:
        """Fix files (not implemented for tests).

        Args:
            paths: List of paths to fix.

        Raises:
            NotImplementedError: Always raised for dummy tool.
        """
        raise NotImplementedError


class _DummyPrettierTool(BaseTool):
    """Dummy prettier tool for testing config injection."""

    name: str = "prettier"
    description: str = "dummy prettier for testing"
    can_fix: bool = True
    config: ToolConfig = ToolConfig(
        priority=1,
        conflicts_with=[],
        file_patterns=["*.js"],
        tool_type=ToolType.FORMATTER,
    )

    def check(self, paths: list[str]) -> Never:
        """Check files (not implemented for tests).

        Args:
            paths: List of paths to check.

        Raises:
            NotImplementedError: Always raised for dummy tool.
        """
        raise NotImplementedError

    def fix(self, paths: list[str]) -> Never:
        """Fix files (not implemented for tests).

        Args:
            paths: List of paths to fix.

        Raises:
            NotImplementedError: Always raised for dummy tool.
        """
        raise NotImplementedError


@pytest.fixture()
def ruff_tool() -> _DummyTool:
    """Provide a dummy ruff tool instance.

    Returns:
        _DummyTool: Configured dummy tool instance.
    """
    return _DummyTool(
        name="ruff",
        description="dummy ruff",
        can_fix=False,
    )


@pytest.fixture()
def prettier_tool() -> _DummyPrettierTool:
    """Provide a dummy prettier tool instance.

    Returns:
        _DummyPrettierTool: Configured dummy tool instance.
    """
    return _DummyPrettierTool(
        name="prettier",
        description="dummy prettier",
        can_fix=True,
    )

    def test_enforce_and_defaults_config_args(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should have both enforce and defaults config args.

        Args:
            self: Test instance.
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
enforce:
  line_length: 88

defaults:
  prettier:
    singleQuote: true
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = prettier_tool._build_config_args()

            # Should have enforce args
            assert_that(args).contains("--print-width")
            assert_that(args).contains("88")
            # Should also have defaults config
            assert_that(args).contains("--config")
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_only_enforce_when_native_config_exists(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should only have enforce args when native config exists.

        Args:
            self: Test instance.
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        # Create native config
        native_config = tmp_path / ".prettierrc"
        native_config.write_text('{"singleQuote": false}')

        config_content = """\
enforce:
  line_length: 100

defaults:
  prettier:
    singleQuote: true
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = prettier_tool._build_config_args()

            # Should have enforce args
            assert_that(args).contains("--print-width")
            assert_that(args).contains("100")
            # Should NOT have defaults config (native exists)
            assert_that(args).does_not_contain("--config")
        finally:
            os.chdir(original_cwd)
            clear_config_cache()
