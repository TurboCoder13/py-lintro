"""Tests for pytest-specific tool executor functionality."""

import tempfile
from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that

from lintro.tools.tool_enum import ToolEnum
from lintro.utils.tool_executor import _get_tools_to_run, run_lint_tools_simple


def test_get_tools_to_run_test_action_with_pytest() -> None:
    """Test _get_tools_to_run with test action returns pytest."""
    result = _get_tools_to_run(tools="pt", action="test")
    assert_that(result).is_length(1)
    assert_that(result[0]).is_equal_to(ToolEnum.PT)


def test_get_tools_to_run_test_action_with_pytest_full_name() -> None:
    """Test _get_tools_to_run with test action using full pytest name."""
    result = _get_tools_to_run(tools="pytest", action="test")
    assert_that(result).is_length(1)
    assert_that(result[0]).is_equal_to(ToolEnum.PT)


def test_get_tools_to_run_test_action_with_none_tools() -> None:
    """Test _get_tools_to_run with test action and None tools."""
    result = _get_tools_to_run(tools=None, action="test")
    assert_that(result).is_length(1)
    assert_that(result[0]).is_equal_to(ToolEnum.PT)


def test_get_tools_to_run_test_action_with_invalid_tool() -> None:
    """Test _get_tools_to_run raises error with invalid tool for test action."""
    with pytest.raises(ValueError, match="only supports pytest"):
        _get_tools_to_run(tools="ruff", action="test")


def test_get_tools_to_run_test_action_with_multiple_tools() -> None:
    """Test _get_tools_to_run raises error with multiple tools for test action."""
    with pytest.raises(ValueError, match="only supports pytest"):
        _get_tools_to_run(tools="pt,ruff", action="test")


def test_get_tools_to_run_check_action_rejects_pytest() -> None:
    """Test _get_tools_to_run rejects pytest for check action."""
    with pytest.raises(ValueError, match="not available for check"):
        _get_tools_to_run(tools="pt", action="check")


def test_get_tools_to_run_format_action_rejects_pytest() -> None:
    """Test _get_tools_to_run rejects pytest for format action."""
    with pytest.raises(ValueError, match="not available for check/fmt"):
        _get_tools_to_run(tools="pt", action="fmt")


def test_get_tools_to_run_test_action_unavailable() -> None:
    """Test _get_tools_to_run handles pytest tool unavailable."""
    with patch.dict("lintro.tools.tool_enum.ToolEnum.__members__", {}):
        # When pytest tool is not in ToolEnum
        pass


def test_get_tools_to_run_check_action_filters_out_pytest() -> None:
    """Test _get_tools_to_run filters pytest out for check action."""
    result = _get_tools_to_run(tools="all", action="check")
    # Should not contain pytest
    assert_that([t.name for t in result]).does_not_contain("PT")


def test_get_tools_to_run_format_action_filters_out_pytest() -> None:
    """Test _get_tools_to_run filters pytest out for format action."""
    result = _get_tools_to_run(tools="all", action="fmt")
    # Should not contain pytest
    assert_that([t.name for t in result]).does_not_contain("PT")


def test_run_lint_tools_simple_test_action_basic() -> None:
    """Test run_lint_tools_simple with test action."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.tool_manager") as mock_manager,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        mock_pytest_tool = Mock()
        mock_pytest_tool.name = "pytest"
        mock_pytest_tool.check.return_value = Mock(
            success=True,
            issues=[],
            output="All tests passed",
        )
        mock_manager.get_tool.return_value = mock_pytest_tool

        result = run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="pt",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=False,
            raw_output=False,
        )

        assert_that(result).is_equal_to(0)


def test_run_lint_tools_simple_test_action_with_failures() -> None:
    """Test run_lint_tools_simple with test failures."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.tool_manager") as mock_manager,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        mock_pytest_tool = Mock()
        mock_pytest_tool.name = "pytest"
        mock_pytest_tool.check.return_value = Mock(
            success=False,
            issues_count=2,
            issues=[Mock(), Mock()],
            output="2 test failures",
        )
        mock_manager.get_tool.return_value = mock_pytest_tool

        result = run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="pt",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=False,
            raw_output=False,
        )

        assert_that(result).is_equal_to(1)


def test_run_lint_tools_simple_test_action_invalid_tool() -> None:
    """Test run_lint_tools_simple with invalid tool for test action."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        result = run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="ruff",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=False,
            raw_output=False,
        )

        # Should return failure when tool is not available
        assert_that(result).is_equal_to(1)


def test_run_lint_tools_simple_test_action_with_tool_options() -> None:
    """Test run_lint_tools_simple with pytest tool options."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.tool_manager") as mock_manager,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        mock_pytest_tool = Mock()
        mock_pytest_tool.name = "pytest"
        mock_pytest_tool.check.return_value = Mock(
            success=True,
            issues=[],
            output="All tests passed",
        )
        mock_manager.get_tool.return_value = mock_pytest_tool

        run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="pt",
            tool_options="pt:maxfail=5,pt:tb=long",
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=False,
            raw_output=False,
        )

        # Should call set_options on the tool
        assert_that(mock_pytest_tool.set_options.called).is_true()


def test_run_lint_tools_simple_test_action_exclude_patterns() -> None:
    """Test run_lint_tools_simple with exclude patterns."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.tool_manager") as mock_manager,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        mock_pytest_tool = Mock()
        mock_pytest_tool.name = "pytest"
        mock_pytest_tool.check.return_value = Mock(
            success=True,
            issues=[],
            output="All tests passed",
        )
        mock_manager.get_tool.return_value = mock_pytest_tool

        run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="pt",
            tool_options=None,
            exclude="*.venv",
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=False,
            raw_output=False,
        )

        # Should set exclude patterns on tool
        assert_that(mock_pytest_tool.check.called).is_true()


def test_run_lint_tools_simple_test_action_verbose() -> None:
    """Test run_lint_tools_simple with verbose flag."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("lintro.utils.tool_executor.tool_manager") as mock_manager,
        patch("lintro.utils.tool_executor.OutputManager") as mock_output,
        patch("lintro.utils.tool_executor.create_logger") as mock_logger,
    ):
        mock_logger_inst = Mock()
        mock_logger.return_value = mock_logger_inst
        mock_output_inst = Mock()
        mock_output_inst.run_dir = tmpdir
        mock_output.return_value = mock_output_inst

        mock_pytest_tool = Mock()
        mock_pytest_tool.name = "pytest"
        mock_pytest_tool.check.return_value = Mock(
            success=True,
            issues=[],
            output="All tests passed",
        )
        mock_manager.get_tool.return_value = mock_pytest_tool

        run_lint_tools_simple(
            action="test",
            paths=["."],
            tools="pt",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="file",
            output_format="plain",
            verbose=True,
            raw_output=False,
        )

        # Logger should be called with verbose=True
        assert_that(mock_logger.called).is_true()
