"""Tests for lintro.tools.core.runtime_discovery module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.tools.core.runtime_discovery import (
    DiscoveredTool,
    _extract_version,
    clear_discovery_cache,
    discover_all_tools,
    discover_tool,
    format_tool_status_table,
    get_available_tools,
    get_tool_path,
    get_unavailable_tools,
    is_tool_available,
)


@pytest.fixture(autouse=True)
def clear_cache_before_each_test() -> None:
    """Clear discovery cache before each test."""
    clear_discovery_cache()


class TestExtractVersion:
    """Tests for _extract_version function."""

    def test_extracts_semantic_version(self) -> None:
        """Extract semantic version from output."""
        assert_that(_extract_version("ruff 0.1.0")).is_equal_to("0.1.0")

    def test_extracts_version_with_prefix(self) -> None:
        """Extract version with v prefix."""
        assert_that(_extract_version("tool v1.2.3")).is_equal_to("1.2.3")

    def test_extracts_version_keyword(self) -> None:
        """Extract version after 'version' keyword."""
        assert_that(_extract_version("black, version 23.0.0")).is_equal_to("23.0.0")

    def test_extracts_from_multiline_output(self) -> None:
        """Extract version from multiline output."""
        output = "mypy 1.0.0 (compiled: yes)\nPython 3.11"
        assert_that(_extract_version(output)).is_equal_to("1.0.0")

    def test_returns_none_for_no_version(self) -> None:
        """Return None when no version found."""
        assert_that(_extract_version("no version here")).is_none()

    def test_returns_none_for_empty_string(self) -> None:
        """Return None for empty string."""
        assert_that(_extract_version("")).is_none()


class TestDiscoverTool:
    """Tests for discover_tool function."""

    def test_discovers_available_tool(self) -> None:
        """Discover tool that exists in PATH."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="ruff 0.1.0",
                stderr="",
            )
            result = discover_tool("ruff", use_cache=False)

            assert_that(result.name).is_equal_to("ruff")
            assert_that(result.path).is_equal_to("/usr/bin/ruff")
            assert_that(result.version).is_equal_to("0.1.0")
            assert_that(result.available).is_true()
            assert_that(result.error_message).is_none()

    def test_discovers_unavailable_tool(self) -> None:
        """Handle tool not found in PATH."""
        with patch("shutil.which", return_value=None):
            result = discover_tool("nonexistent", use_cache=False)

            assert_that(result.name).is_equal_to("nonexistent")
            assert_that(result.path).is_equal_to("")
            assert_that(result.available).is_false()
            assert_that(result.error_message).contains("not found in PATH")

    def test_handles_version_check_timeout(self) -> None:
        """Handle timeout during version check."""
        import subprocess

        with (
            patch("shutil.which", return_value="/usr/bin/slow_tool"),
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["tool"], timeout=5),
            ),
        ):
            result = discover_tool("slow_tool", use_cache=False)

            assert_that(result.available).is_true()
            assert_that(result.path).is_equal_to("/usr/bin/slow_tool")
            assert_that(result.version).is_none()

    def test_handles_version_check_oserror(self) -> None:
        """Handle OSError during version check."""
        with (
            patch("shutil.which", return_value="/usr/bin/broken_tool"),
            patch("subprocess.run", side_effect=OSError("Permission denied")),
        ):
            result = discover_tool("broken_tool", use_cache=False)

            assert_that(result.available).is_true()
            assert_that(result.version).is_none()

    def test_uses_cache_by_default(self) -> None:
        """Use cache by default on second call."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="ruff 0.1.0")

            # First call
            discover_tool("ruff")
            # Second call should use cache
            discover_tool("ruff")

            # shutil.which should only be called once (cached)
            assert_that(mock_which.call_count).is_equal_to(1)

    def test_bypasses_cache_when_disabled(self) -> None:
        """Bypass cache when use_cache=False."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="ruff 0.1.0")

            # Both calls should hit shutil.which
            discover_tool("ruff", use_cache=False)
            discover_tool("ruff", use_cache=False)

            assert_that(mock_which.call_count).is_equal_to(2)

    def test_extracts_version_from_stderr(self) -> None:
        """Extract version from stderr when stdout is empty."""
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="tool 2.0.0",
            )
            result = discover_tool("tool", use_cache=False)

            assert_that(result.version).is_equal_to("2.0.0")


class TestDiscoverAllTools:
    """Tests for discover_all_tools function."""

    def test_discovers_all_configured_tools(self) -> None:
        """Discover all tools in TOOL_VERSION_COMMANDS."""
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0")

            tools = discover_all_tools(use_cache=False)

            # Should have discovered multiple tools
            assert_that(len(tools)).is_greater_than(5)
            assert_that(tools).contains_key("ruff", "black", "mypy")

    def test_uses_cache_on_second_call(self) -> None:
        """Use cache on second call."""
        with (
            patch("shutil.which", return_value="/usr/bin/tool") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0")

            discover_all_tools(use_cache=False)
            initial_call_count = mock_which.call_count

            # Second call should use cache
            discover_all_tools()

            assert_that(mock_which.call_count).is_equal_to(initial_call_count)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_is_tool_available_returns_true(self) -> None:
        """is_tool_available returns True for available tool."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="ruff 0.1.0")

            assert_that(is_tool_available("ruff")).is_true()

    def test_is_tool_available_returns_false(self) -> None:
        """is_tool_available returns False for unavailable tool."""
        with patch("shutil.which", return_value=None):
            assert_that(is_tool_available("nonexistent")).is_false()

    def test_get_tool_path_returns_path(self) -> None:
        """get_tool_path returns path for available tool."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="ruff 0.1.0")

            assert_that(get_tool_path("ruff")).is_equal_to("/usr/bin/ruff")

    def test_get_tool_path_returns_none(self) -> None:
        """get_tool_path returns None for unavailable tool."""
        with patch("shutil.which", return_value=None):
            assert_that(get_tool_path("nonexistent")).is_none()

    def test_get_unavailable_tools(self) -> None:
        """get_unavailable_tools returns list of missing tools."""

        def mock_which(name: str) -> str | None:
            return "/usr/bin/ruff" if name == "ruff" else None

        with (
            patch("shutil.which", side_effect=mock_which),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0")

            unavailable = get_unavailable_tools()

            # ruff should NOT be in unavailable list
            assert_that(unavailable).does_not_contain("ruff")
            # Other tools should be unavailable
            assert_that(len(unavailable)).is_greater_than(0)

    def test_get_available_tools(self) -> None:
        """get_available_tools returns list of available tools."""

        def mock_which(name: str) -> str | None:
            return "/usr/bin/ruff" if name == "ruff" else None

        with (
            patch("shutil.which", side_effect=mock_which),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0")

            available = get_available_tools()

            # ruff should be in available list
            assert_that(available).contains("ruff")


class TestFormatToolStatusTable:
    """Tests for format_tool_status_table function."""

    def test_formats_table_with_tools(self) -> None:
        """Format status table with discovered tools."""
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="1.0.0")

            table = format_tool_status_table()

            assert_that(table).contains("Tool Discovery Status")
            assert_that(table).contains("Available")
            assert_that(table).contains("ruff")

    def test_shows_missing_tools(self) -> None:
        """Show missing tools in table."""
        with (
            patch("shutil.which", return_value=None),
            patch("subprocess.run"),
        ):
            table = format_tool_status_table()

            assert_that(table).contains("Missing")


class TestClearDiscoveryCache:
    """Tests for clear_discovery_cache function."""

    def test_clears_cache(self) -> None:
        """Clear cache makes next call rediscover tools."""
        with (
            patch("shutil.which", return_value="/usr/bin/ruff") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="ruff 0.1.0")

            # First discovery
            discover_tool("ruff")
            initial_count = mock_which.call_count

            # Clear cache
            clear_discovery_cache()

            # Should rediscover
            discover_tool("ruff")
            assert_that(mock_which.call_count).is_equal_to(initial_count + 1)


class TestDiscoveredToolDataclass:
    """Tests for DiscoveredTool dataclass."""

    def test_default_values(self) -> None:
        """DiscoveredTool has correct defaults."""
        tool = DiscoveredTool(name="test")

        assert_that(tool.name).is_equal_to("test")
        assert_that(tool.path).is_equal_to("")
        assert_that(tool.version).is_none()
        assert_that(tool.available).is_true()
        assert_that(tool.error_message).is_none()

    def test_all_fields_set(self) -> None:
        """DiscoveredTool accepts all fields."""
        tool = DiscoveredTool(
            name="ruff",
            path="/usr/bin/ruff",
            version="0.1.0",
            available=True,
            error_message=None,
        )

        assert_that(tool.name).is_equal_to("ruff")
        assert_that(tool.path).is_equal_to("/usr/bin/ruff")
        assert_that(tool.version).is_equal_to("0.1.0")
