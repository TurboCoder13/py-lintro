"""Tests for the simplified runner module."""

import pytest
from unittest.mock import patch, MagicMock
from tempfile import TemporaryDirectory
from pathlib import Path

from lintro.utils.tool_executor import (
    _get_tools_to_run,
    _parse_tool_options,
    run_lint_tools_simple,
)
from lintro.tools.tool_enum import ToolEnum


@pytest.mark.utils
def test_get_tools_to_run_all():
    """Test getting all available tools."""
    mock_check_tools = {ToolEnum.RUFF: MagicMock(), ToolEnum.YAMLLINT: MagicMock()}
    mock_fix_tools = {ToolEnum.RUFF: MagicMock(), ToolEnum.PRETTIER: MagicMock()}

    with patch("lintro.utils.tool_executor.tool_manager") as mock_manager:
        mock_manager.get_check_tools.return_value = mock_check_tools
        mock_manager.get_fix_tools.return_value = mock_fix_tools

        # Test check action with "all"
        result = _get_tools_to_run("all", "check")
        assert result == list(mock_check_tools.keys())

        # Test fmt action with "all"
        result = _get_tools_to_run("all", "fmt")
        assert result == list(mock_fix_tools.keys())


@pytest.mark.utils
def test_get_tools_to_run_none():
    """Test getting all tools when tools is None."""
    mock_check_tools = {ToolEnum.RUFF: MagicMock()}

    with patch("lintro.utils.tool_executor.tool_manager") as mock_manager:
        mock_manager.get_check_tools.return_value = mock_check_tools

        result = _get_tools_to_run(None, "check")
        assert result == list(mock_check_tools.keys())


@pytest.mark.utils
def test_get_tools_to_run_specific():
    """Test getting specific tools."""
    result = _get_tools_to_run("ruff,yamllint", "check")
    assert ToolEnum.RUFF in result
    assert ToolEnum.YAMLLINT in result
    assert len(result) == 2


@pytest.mark.utils
def test_get_tools_to_run_invalid():
    """Test getting tools with invalid tool name."""
    with pytest.raises(ValueError, match="Unknown tool 'invalid'"):
        _get_tools_to_run("ruff,invalid", "check")


@pytest.mark.utils
def test_get_tools_to_run_format_unsupported():
    """Test getting tools that don't support formatting."""
    with patch("lintro.utils.tool_executor.tool_manager") as mock_manager:
        mock_tool = MagicMock()
        mock_tool.can_fix = False
        mock_manager.get_tool.return_value = mock_tool

        with pytest.raises(ValueError, match="does not support formatting"):
            _get_tools_to_run("yamllint", "fmt")


@pytest.mark.utils
def test_parse_tool_options_basic():
    """Test parsing basic tool options."""
    result = _parse_tool_options("ruff:line-length=120,prettier:tab-width=2")

    expected = {"ruff": {"line-length": "120"}, "prettier": {"tab-width": "2"}}
    assert result == expected


@pytest.mark.utils
def test_parse_tool_options_empty():
    """Test parsing empty tool options."""
    assert _parse_tool_options(None) == {}
    assert _parse_tool_options("") == {}


@pytest.mark.utils
def test_parse_tool_options_invalid_format():
    """Test parsing tool options with invalid format."""
    # Should ignore invalid formats
    result = _parse_tool_options("invalid,ruff:line-length=120")
    expected = {"ruff": {"line-length": "120"}}
    assert result == expected


@pytest.mark.utils
def test_run_lint_tools_simple_success():
    """Test successful run of lint tools."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor.tool_manager"
                ) as mock_tool_manager:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger

                    mock_tool = MagicMock()
                    mock_result = MagicMock()
                    mock_result.issues_count = 0
                    mock_result.output = ""
                    mock_tool.check.return_value = mock_result
                    mock_tool_manager.get_tool.return_value = mock_tool

                    # Run the function
                    exit_code = run_lint_tools_simple(
                        action="check",
                        paths=["src/"],
                        tools="ruff",
                        tool_options=None,
                        exclude=None,
                        include_venv=False,
                        group_by="auto",
                        output_format="grid",
                        verbose=False,
                    )

                    # Assertions
                    assert exit_code == 0
                    mock_logger.print_lintro_header.assert_called_once()
                    mock_logger.print_tool_header.assert_called_once()
                    mock_logger.print_execution_summary.assert_called_once()


@pytest.mark.utils
def test_run_lint_tools_simple_with_issues():
    """Test run with issues found."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor.tool_manager"
                ) as mock_tool_manager:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger

                    mock_tool = MagicMock()
                    mock_result = MagicMock()
                    mock_result.issues_count = 5
                    mock_result.output = "Some issues found"
                    mock_tool.check.return_value = mock_result
                    mock_tool_manager.get_tool.return_value = mock_tool

                    # Run the function
                    exit_code = run_lint_tools_simple(
                        action="check",
                        paths=["src/"],
                        tools="ruff",
                        tool_options=None,
                        exclude=None,
                        include_venv=False,
                        group_by="auto",
                        output_format="grid",
                        verbose=False,
                    )

                    # Check operation should return 1 for issues
                    assert exit_code == 1


@pytest.mark.utils
def test_run_lint_tools_simple_format_action():
    """Test format action always returns 0."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor.tool_manager"
                ) as mock_tool_manager:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger

                    mock_tool = MagicMock()
                    mock_result = MagicMock()
                    mock_result.issues_count = 5  # Even with issues
                    mock_result.output = "Fixed some issues"
                    mock_tool.fix.return_value = mock_result
                    mock_tool_manager.get_tool.return_value = mock_tool

                    # Run the function
                    exit_code = run_lint_tools_simple(
                        action="fmt",
                        paths=["src/"],
                        tools="ruff",
                        tool_options=None,
                        exclude=None,
                        include_venv=False,
                        group_by="auto",
                        output_format="grid",
                        verbose=False,
                    )

                    # Format action should always return 0
                    assert exit_code == 0
                    mock_tool.fix.assert_called_once()


@pytest.mark.utils
def test_run_lint_tools_simple_invalid_tools():
    """Test handling of invalid tools."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                # Setup mocks
                mock_output_manager.return_value.run_dir = Path(temp_dir)
                mock_logger = MagicMock()
                mock_create_logger.return_value = mock_logger

                # Run with invalid tool
                exit_code = run_lint_tools_simple(
                    action="check",
                    paths=["src/"],
                    tools="invalid_tool",
                    tool_options=None,
                    exclude=None,
                    include_venv=False,
                    group_by="auto",
                    output_format="grid",
                    verbose=False,
                )

                assert exit_code == 1
                mock_logger.error.assert_called()


@pytest.mark.utils
def test_run_lint_tools_simple_no_tools():
    """Test handling when no tools are found."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor._get_tools_to_run"
                ) as mock_get_tools:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger
                    mock_get_tools.return_value = []  # No tools

                    # Run the function
                    exit_code = run_lint_tools_simple(
                        action="check",
                        paths=["src/"],
                        tools="ruff",
                        tool_options=None,
                        exclude=None,
                        include_venv=False,
                        group_by="auto",
                        output_format="grid",
                        verbose=False,
                    )

                    assert exit_code == 1
                    mock_logger.warning.assert_called_with("No tools found to run")


@pytest.mark.utils
def test_run_lint_tools_simple_tool_error():
    """Test handling of tool execution errors."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor.tool_manager"
                ) as mock_tool_manager:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger

                    mock_tool = MagicMock()
                    mock_tool.check.side_effect = Exception("Tool failed")
                    mock_tool_manager.get_tool.return_value = mock_tool

                    # Run the function
                    exit_code = run_lint_tools_simple(
                        action="check",
                        paths=["src/"],
                        tools="ruff",
                        tool_options=None,
                        exclude=None,
                        include_venv=False,
                        group_by="auto",
                        output_format="grid",
                        verbose=False,
                    )

                    assert exit_code == 1
                    mock_logger.error.assert_called()


@pytest.mark.utils
def test_run_lint_tools_simple_with_options():
    """Test run with tool options and exclude patterns."""
    with TemporaryDirectory() as temp_dir:
        with patch("lintro.utils.tool_executor.OutputManager") as mock_output_manager:
            with patch(
                "lintro.utils.tool_executor.create_logger"
            ) as mock_create_logger:
                with patch(
                    "lintro.utils.tool_executor.tool_manager"
                ) as mock_tool_manager:
                    # Setup mocks
                    mock_output_manager.return_value.run_dir = Path(temp_dir)
                    mock_logger = MagicMock()
                    mock_create_logger.return_value = mock_logger

                    mock_tool = MagicMock()
                    mock_result = MagicMock()
                    mock_result.issues_count = 0
                    mock_result.output = ""
                    mock_tool.check.return_value = mock_result
                    mock_tool_manager.get_tool.return_value = mock_tool

                    # Run the function with options
                    exit_code = run_lint_tools_simple(
                        action="check",
                        paths=["src/"],
                        tools="ruff",
                        tool_options="ruff:line-length=120",
                        exclude="*.pyc,__pycache__",
                        include_venv=True,
                        group_by="file",
                        output_format="json",
                        verbose=True,
                    )

                    assert exit_code == 0
                    # Verify tool was configured with options
                    mock_tool.set_options.assert_called()

                    # Check that exclude patterns were set
                    calls = mock_tool.set_options.call_args_list
                    assert any("exclude_patterns" in str(call) for call in calls)
                    assert any("include_venv" in str(call) for call in calls)
