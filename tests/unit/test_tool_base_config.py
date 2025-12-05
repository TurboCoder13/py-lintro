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


class TestGetEnforceCliArgs:
    """Tests for _get_enforce_cli_args method."""

    def test_returns_empty_when_no_config(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
    ) -> None:
        """Should return empty list when no lintro config exists.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            # No config file, so should return empty
            args = ruff_tool._get_enforce_cli_args()
            assert args == []
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_line_length_for_ruff(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
    ) -> None:
        """Should return --line-length for ruff when enforce.line_length set.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
enforce:
  line_length: 100
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = ruff_tool._get_enforce_cli_args()
            assert "--line-length" in args
            assert "100" in args
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_target_version_for_ruff(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
    ) -> None:
        """Should return --target-version for ruff when enforce.target_python set.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
enforce:
  target_python: py313
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = ruff_tool._get_enforce_cli_args()
            assert "--target-version" in args
            assert "py313" in args
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_print_width_for_prettier(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should return --print-width for prettier when enforce.line_length set.

        Args:
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
enforce:
  line_length: 120
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = prettier_tool._get_enforce_cli_args()
            assert "--print-width" in args
            assert "120" in args
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_skips_injection_when_env_var_set(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should skip injection when LINTRO_SKIP_CONFIG_INJECTION is set.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
            monkeypatch: Pytest monkeypatch fixture.
        """
        config_content = """\
enforce:
  line_length: 100
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        monkeypatch.setenv("LINTRO_SKIP_CONFIG_INJECTION", "1")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = ruff_tool._get_enforce_cli_args()
            assert args == []
        finally:
            os.chdir(original_cwd)
            clear_config_cache()


class TestGetDefaultsConfigArgs:
    """Tests for _get_defaults_config_args method."""

    def test_returns_empty_when_no_defaults(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should return empty list when no defaults defined.

        Args:
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
enforce:
  line_length: 88
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = prettier_tool._get_defaults_config_args()
            assert args == []
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_config_when_defaults_defined_no_native(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should return --config when defaults defined and no native config.

        Args:
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
defaults:
  prettier:
    singleQuote: true
    tabWidth: 2
"""
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            args = prettier_tool._get_defaults_config_args()
            assert "--config" in args
            # Should have a path to temp file
            assert len(args) == 2
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_empty_when_native_config_exists(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should return empty when native config exists (native wins).

        Args:
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        # Create native config
        native_config = tmp_path / ".prettierrc"
        native_config.write_text('{"singleQuote": false}')

        config_content = """\
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

            args = prettier_tool._get_defaults_config_args()
            # Should be empty because native config exists
            assert args == []
        finally:
            os.chdir(original_cwd)
            clear_config_cache()


class TestBuildConfigArgs:
    """Tests for _build_config_args method."""

    def test_combines_enforce_and_defaults(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """Should combine enforce CLI args and defaults config args.

        Args:
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
            assert "--print-width" in args
            assert "88" in args

            # Should also have defaults config
            assert "--config" in args
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
            assert "--print-width" in args
            assert "100" in args

            # Should NOT have defaults config (native exists)
            assert "--config" not in args
        finally:
            os.chdir(original_cwd)
            clear_config_cache()


class TestShouldUseLintroConfig:
    """Tests for _should_use_lintro_config method."""

    def test_returns_false_when_no_config(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
    ) -> None:
        """Should return False when no lintro config exists.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            result = ruff_tool._should_use_lintro_config()
            assert result is False
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_true_when_config_exists(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
    ) -> None:
        """Should return True when lintro config exists.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
        """
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text("enforce: {}")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            result = ruff_tool._should_use_lintro_config()
            assert result is True
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_returns_false_when_env_var_set(
        self,
        ruff_tool: _DummyTool,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should return False when LINTRO_SKIP_CONFIG_INJECTION is set.

        Args:
            ruff_tool: Dummy ruff tool instance.
            tmp_path: Temporary directory for test.
            monkeypatch: Pytest monkeypatch fixture.
        """
        config_file = tmp_path / ".lintro-config.yaml"
        config_file.write_text("enforce: {}")

        monkeypatch.setenv("LINTRO_SKIP_CONFIG_INJECTION", "1")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            clear_config_cache()

            result = ruff_tool._should_use_lintro_config()
            assert result is False
        finally:
            os.chdir(original_cwd)
            clear_config_cache()


class TestDeprecatedMethods:
    """Tests for deprecated backward compatibility methods."""

    def test_generate_tool_config_deprecated(
        self,
        prettier_tool: _DummyPrettierTool,
        tmp_path: Path,
    ) -> None:
        """_generate_tool_config should still work but use generate_defaults_config.

        Args:
            prettier_tool: Dummy prettier tool instance.
            tmp_path: Temporary directory for test.
        """
        config_content = """\
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

            # Deprecated method should still work
            result = prettier_tool._generate_tool_config()
            # May return None or Path depending on defaults
            assert result is None or isinstance(result, Path)
        finally:
            os.chdir(original_cwd)
            clear_config_cache()

    def test_get_no_auto_config_args_returns_empty(
        self,
        ruff_tool: _DummyTool,
    ) -> None:
        """_get_no_auto_config_args should return empty (deprecated).

        Args:
            ruff_tool: Dummy ruff tool instance.
        """
        args = ruff_tool._get_no_auto_config_args()
        assert args == []
