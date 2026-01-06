"""Unit tests for config_reporting module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.utils.config_reporting import get_config_report, print_config_report


@pytest.fixture
def mock_tool_config_summary() -> dict[str, Any]:
    """Create mock tool config summary.

    Returns:
        Dictionary containing mock tool config summary.
    """
    mock_info = MagicMock()
    mock_info.is_injectable = True
    mock_info.effective_config = {"line_length": 88}
    mock_info.lintro_tool_config = {"line_length": 88}
    mock_info.native_config = None
    return {"ruff": mock_info}


@pytest.fixture
def standard_patches(mock_tool_config_summary: dict[str, Any]) -> tuple[Any, ...]:
    """Provide standard patches for get_config_report tests.

    Args:
        mock_tool_config_summary: Mock tool config summary fixture.

    Returns:
        Tuple of patch objects for testing.
    """
    return (
        patch(
            "lintro.utils.unified_config.get_tool_config_summary",
            return_value=mock_tool_config_summary,
        ),
        patch(
            "lintro.utils.config_reporting.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_order_config",
            return_value={"strategy": "priority"},
        ),
        patch(
            "lintro.utils.config_reporting.get_ordered_tools",
            return_value=["ruff"],
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_priority",
            return_value=100,
        ),
        patch(
            "lintro.utils.config_reporting.validate_config_consistency",
            return_value=[],
        ),
    )


# --- get_config_report tests ---


def test_report_contains_header(standard_patches: tuple[Any, ...]) -> None:
    """Test report contains header section.

    Args:
        standard_patches: Standard patches for testing.
    """
    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        standard_patches[5],
    ):
        report = get_config_report()

        assert_that(report).contains("LINTRO CONFIGURATION REPORT")
        assert_that(report).contains("=" * 60)


def test_report_contains_global_settings(standard_patches: tuple[Any, ...]) -> None:
    """Test report contains global settings section.

    Args:
        standard_patches: Standard patches for testing.
    """
    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        standard_patches[5],
    ):
        report = get_config_report()

        assert_that(report).contains("── Global Settings ──")
        assert_that(report).contains("Central line_length: 88")
        assert_that(report).contains("Tool order strategy: priority")


def test_report_contains_tool_execution_order(
    standard_patches: tuple[Any, ...],
) -> None:
    """Test report contains tool execution order section.

    Args:
        standard_patches: Standard patches for testing.
    """
    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        standard_patches[5],
    ):
        report = get_config_report()

        assert_that(report).contains("── Tool Execution Order ──")
        assert_that(report).contains("1. ruff (priority: 100)")


def test_report_contains_per_tool_config(standard_patches: tuple[Any, ...]) -> None:
    """Test report contains per-tool configuration section.

    Args:
        standard_patches: Standard patches for testing.
    """
    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        standard_patches[5],
    ):
        report = get_config_report()

        assert_that(report).contains("── Per-Tool Configuration ──")
        assert_that(report).contains("ruff:")
        assert_that(report).contains("Status: ✅ Syncable")
        assert_that(report).contains("Effective line_length: 88")


def test_report_shows_native_only_for_non_injectable() -> None:
    """Test non-injectable tools show native only status."""
    mock_info = MagicMock()
    mock_info.is_injectable = False
    mock_info.effective_config = {"line_length": 80}
    mock_info.lintro_tool_config = None
    mock_info.native_config = {"some": "config"}

    with (
        patch(
            "lintro.utils.unified_config.get_tool_config_summary",
            return_value={"prettier": mock_info},
        ),
        patch(
            "lintro.utils.config_reporting.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_order_config",
            return_value={"strategy": "priority"},
        ),
        patch(
            "lintro.utils.config_reporting.get_ordered_tools",
            return_value=["prettier"],
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_priority",
            return_value=50,
        ),
        patch(
            "lintro.utils.config_reporting.validate_config_consistency",
            return_value=[],
        ),
    ):
        report = get_config_report()
        assert_that(report).contains("Status: ⚠️ Native only")


def test_report_shows_warnings(standard_patches: tuple[Any, ...]) -> None:
    """Test report shows warnings when present.

    Args:
        standard_patches: Standard patches for testing.
    """
    warnings = ["Warning 1: Config mismatch", "Warning 2: Missing config"]

    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        patch(
            "lintro.utils.config_reporting.validate_config_consistency",
            return_value=warnings,
        ),
    ):
        report = get_config_report()

        assert_that(report).contains("── Configuration Warnings ──")
        assert_that(report).contains("Warning 1: Config mismatch")
        assert_that(report).contains("Warning 2: Missing config")


def test_report_shows_no_warnings_message(standard_patches: tuple[Any, ...]) -> None:
    """Test report shows no warnings message when consistent.

    Args:
        standard_patches: Standard patches for testing.
    """
    with (
        standard_patches[0],
        standard_patches[1],
        standard_patches[2],
        standard_patches[3],
        standard_patches[4],
        standard_patches[5],
    ):
        report = get_config_report()
        assert_that(report).contains("None - all configs consistent!")


def test_report_with_custom_order(mock_tool_config_summary: dict[str, Any]) -> None:
    """Test report shows custom order when configured.

    Args:
        mock_tool_config_summary: Mock tool config summary.
    """
    with (
        patch(
            "lintro.utils.unified_config.get_tool_config_summary",
            return_value=mock_tool_config_summary,
        ),
        patch(
            "lintro.utils.config_reporting.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_order_config",
            return_value={"strategy": "custom", "custom_order": ["ruff", "mypy"]},
        ),
        patch(
            "lintro.utils.config_reporting.get_ordered_tools",
            return_value=["ruff"],
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_priority",
            return_value=100,
        ),
        patch(
            "lintro.utils.config_reporting.validate_config_consistency",
            return_value=[],
        ),
    ):
        report = get_config_report()
        assert_that(report).contains("Custom order: ruff, mypy")


def test_report_line_length_not_configured(
    mock_tool_config_summary: dict[str, Any],
) -> None:
    """Test report shows Not configured when line_length is None.

    Args:
        mock_tool_config_summary: Mock tool config summary.
    """
    with (
        patch(
            "lintro.utils.unified_config.get_tool_config_summary",
            return_value=mock_tool_config_summary,
        ),
        patch(
            "lintro.utils.config_reporting.get_effective_line_length",
            return_value=None,
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_order_config",
            return_value={"strategy": "priority"},
        ),
        patch(
            "lintro.utils.config_reporting.get_ordered_tools",
            return_value=["ruff"],
        ),
        patch(
            "lintro.utils.config_reporting.get_tool_priority",
            return_value=100,
        ),
        patch(
            "lintro.utils.config_reporting.validate_config_consistency",
            return_value=[],
        ),
    ):
        report = get_config_report()
        assert_that(report).contains("Central line_length: Not configured")


# --- print_config_report tests ---


def test_print_logs_report_lines() -> None:
    """Test that report lines are logged."""
    mock_report = "── Global Settings ──\n  line_length: 88\n── End ──"

    with (
        patch(
            "lintro.utils.config_reporting.get_config_report",
            return_value=mock_report,
        ),
        patch("lintro.utils.config_reporting.logger") as mock_logger,
    ):
        print_config_report()
        assert_that(mock_logger.info.called).is_true()


def test_print_warnings_logged_at_warning_level() -> None:
    """Test that warnings section lines are logged at warning level."""
    mock_report = (
        "── Configuration Warnings ──\n" "  Warning: Config mismatch\n" "── End ──"
    )

    with (
        patch(
            "lintro.utils.config_reporting.get_config_report",
            return_value=mock_report,
        ),
        patch("lintro.utils.config_reporting.logger") as mock_logger,
    ):
        print_config_report()
        warning_calls = list(mock_logger.warning.call_args_list)
        assert_that(len(warning_calls)).is_greater_than(0)


def test_print_non_warning_lines_logged_at_info() -> None:
    """Test that non-warning lines are logged at info level."""
    mock_report = "── Global Settings ──\n  line_length: 88"

    with (
        patch(
            "lintro.utils.config_reporting.get_config_report",
            return_value=mock_report,
        ),
        patch("lintro.utils.config_reporting.logger") as mock_logger,
    ):
        print_config_report()
        assert_that(mock_logger.info.called).is_true()
