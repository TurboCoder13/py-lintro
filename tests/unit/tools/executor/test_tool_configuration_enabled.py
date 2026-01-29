"""Tests for tool enabled/disabled functionality in get_tools_to_run.

These tests verify that tools marked as disabled in .lintro-config.yaml
are properly filtered out of the tools list.

Covers:
- Disabled tools being skipped with `enabled: false` format
- Disabled tools being skipped with shorthand `toolname: false` format
- Enabled tools running normally
- Mixed enabled/disabled scenarios
- Both "all" tools and specific tool selection
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.config.config_loader import clear_config_cache
from lintro.config.execution_config import ExecutionConfig
from lintro.config.lintro_config import LintroConfig, LintroToolConfig
from lintro.utils.execution.tool_configuration import get_tools_to_run


class FakeToolDefinition:
    """Fake ToolDefinition for testing."""

    def __init__(self, name: str, can_fix: bool = True) -> None:
        """Initialize FakeToolDefinition.

        Args:
            name: Name of the tool.
            can_fix: Whether the tool supports fixing.
        """
        self.name = name
        self.can_fix = can_fix
        self.description = ""
        self.file_patterns: list[str] = []
        self.native_configs: list[str] = []


class FakeTool:
    """Fake tool for testing."""

    def __init__(self, name: str, can_fix: bool = True) -> None:
        """Initialize FakeTool.

        Args:
            name: Name of the tool.
            can_fix: Whether the tool supports fixing.
        """
        self._definition = FakeToolDefinition(name=name, can_fix=can_fix)

    @property
    def definition(self) -> FakeToolDefinition:
        """Get the tool definition."""
        return self._definition

    def set_options(self, **kwargs: Any) -> None:
        """Set tool options (no-op for fake tool)."""
        pass


@pytest.fixture(autouse=True)
def reset_config_cache() -> None:
    """Reset config cache before each test."""
    clear_config_cache()


class TestGetToolsToRunDisabledTools:
    """Test get_tools_to_run with disabled tools."""

    def test_disabled_tool_skipped_in_all_tools_check(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Disabled tool should be skipped when using 'all' for check action."""
        from lintro.tools import tool_manager

        # Mock tool_manager to return known tools
        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy", "bandit"],
        )

        # Create config with mypy disabled
        config = LintroConfig(
            tools={
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).contains("ruff", "bandit")
        assert_that(result).does_not_contain("mypy")

    def test_disabled_tool_skipped_in_all_tools_fix(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Disabled tool should be skipped when using 'all' for fix action."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_fix_tools",
            lambda: ["ruff", "black", "prettier"],
        )

        # Create config with black disabled using shorthand format
        config = LintroConfig(
            tools={
                "black": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools="all", action="fmt")

        assert_that(result).contains("ruff", "prettier")
        assert_that(result).does_not_contain("black")

    def test_disabled_tool_skipped_when_explicitly_requested(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Disabled tool should be skipped even when explicitly requested."""
        from lintro.tools import tool_manager

        # Mock tool registration check
        monkeypatch.setattr(
            tool_manager,
            "is_tool_registered",
            lambda name: name in ["ruff", "mypy"],
        )
        monkeypatch.setattr(
            tool_manager,
            "get_tool_names",
            lambda: ["ruff", "mypy"],
        )

        # Create config with mypy disabled
        config = LintroConfig(
            tools={
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools="ruff,mypy", action="check")

        assert_that(result).is_equal_to(["ruff"])
        assert_that(result).does_not_contain("mypy")

    def test_all_tools_disabled_returns_empty_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When all available tools are disabled, return empty list."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy"],
        )

        # Disable all tools
        config = LintroConfig(
            tools={
                "ruff": LintroToolConfig(enabled=False),
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).is_empty()

    def test_enabled_tool_runs_normally(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicitly enabled tool should run normally."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy"],
        )

        # Explicitly enable ruff, disable mypy
        config = LintroConfig(
            tools={
                "ruff": LintroToolConfig(enabled=True),
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).is_equal_to(["ruff"])

    def test_tool_not_in_config_defaults_to_enabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Tools not explicitly configured should default to enabled."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy", "bandit"],
        )

        # Only configure mypy as disabled, others should default to enabled
        config = LintroConfig(
            tools={
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).contains("ruff", "bandit")
        assert_that(result).does_not_contain("mypy")

    def test_empty_config_all_tools_enabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty config should have all tools enabled by default."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy", "bandit"],
        )

        # Empty config - all tools should be enabled
        config = LintroConfig()

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).contains("ruff", "mypy", "bandit")


class TestGetToolsToRunExecutionEnabledTools:
    """Test get_tools_to_run with execution.enabled_tools filter."""

    def test_execution_enabled_tools_filter(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Only tools in execution.enabled_tools should run."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy", "bandit"],
        )

        # Restrict to only ruff via execution.enabled_tools
        config = LintroConfig(
            execution=ExecutionConfig(enabled_tools=["ruff"]),
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).is_equal_to(["ruff"])

    def test_execution_enabled_tools_combined_with_tool_disabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Both execution.enabled_tools and tools.enabled should be checked."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "mypy", "bandit"],
        )

        # Allow ruff and mypy via execution.enabled_tools, but disable mypy
        config = LintroConfig(
            execution=ExecutionConfig(enabled_tools=["ruff", "mypy"]),
            tools={
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).is_equal_to(["ruff"])


class TestGetToolsToRunSpecificToolsWithFix:
    """Test get_tools_to_run with specific tools and fix action."""

    def test_disabled_tool_skipped_in_fix_action(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Disabled tool should be skipped for fix action."""
        from lintro.tools import tool_manager

        fake_ruff = FakeTool(name="ruff", can_fix=True)
        fake_black = FakeTool(name="black", can_fix=True)

        def mock_get_tool(name: str) -> FakeTool:
            if name == "ruff":
                return fake_ruff
            if name == "black":
                return fake_black
            raise ValueError(f"Unknown tool: {name}")

        monkeypatch.setattr(
            tool_manager,
            "is_tool_registered",
            lambda name: name in ["ruff", "black"],
        )
        monkeypatch.setattr(tool_manager, "get_tool", mock_get_tool)
        monkeypatch.setattr(
            tool_manager,
            "get_tool_names",
            lambda: ["ruff", "black"],
        )

        # Disable black
        config = LintroConfig(
            tools={
                "black": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools="ruff,black", action="fmt")

        assert_that(result).is_equal_to(["ruff"])
        assert_that(result).does_not_contain("black")


class TestGetToolsToRunCaseInsensitivity:
    """Test that tool name matching is case-insensitive."""

    def test_disabled_tool_case_insensitive(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Tool enabled check should be case-insensitive."""
        from lintro.tools import tool_manager

        monkeypatch.setattr(
            tool_manager,
            "get_check_tools",
            lambda: ["ruff", "MyPy"],  # Mixed case from tool_manager
        )

        # Config uses lowercase
        config = LintroConfig(
            tools={
                "mypy": LintroToolConfig(enabled=False),
            },
        )

        with patch(
            "lintro.utils.execution.tool_configuration.get_config",
            return_value=config,
        ):
            result = get_tools_to_run(tools=None, action="check")

        assert_that(result).is_equal_to(["ruff"])
        # MyPy should be filtered regardless of case
        assert_that(result).does_not_contain("MyPy")
        assert_that(result).does_not_contain("mypy")
