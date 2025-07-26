"""Tests for the simplified Loguru logger module."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from lintro.utils.console_logger import (
    SimpleLintroLogger,
    create_logger,
    get_tool_emoji,
)


@pytest.mark.utils
def test_get_tool_emoji():
    """Test getting emoji for different tools."""
    assert get_tool_emoji("ruff") == "🦀"
    assert get_tool_emoji("prettier") == "💅"
    assert get_tool_emoji("darglint") == "📝"
    assert get_tool_emoji("hadolint") == "🐳"
    assert get_tool_emoji("yamllint") == "📄"
    assert get_tool_emoji("unknown_tool") == "🔧"


@pytest.mark.utils
def test_create_logger():
    """Test creating a SimpleLintroLogger instance."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = create_logger(run_dir=run_dir, verbose=True)

        assert isinstance(logger, SimpleLintroLogger)
        assert logger.run_dir == run_dir
        assert logger.verbose is True


@pytest.mark.utils
def test_simple_lintro_logger_init():
    """Test SimpleLintroLogger initialization."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir, verbose=False)

        assert logger.run_dir == run_dir
        assert logger.verbose is False
        assert logger.console_messages == []


@pytest.mark.utils
def test_console_output():
    """Test console output functionality."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch("click.echo") as mock_echo:
            logger.console_output("Test message")

        mock_echo.assert_called_once_with("Test message")
        assert "Test message" in logger.console_messages


@pytest.mark.utils
def test_console_output_with_color():
    """Test console output with color."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch("click.echo") as mock_echo:
            with patch("click.style") as mock_style:
                mock_style.return_value = "styled_message"
                logger.console_output("Test message", color="green")

        mock_style.assert_called_once_with("Test message", fg="green")
        mock_echo.assert_called_once_with("styled_message")


@pytest.mark.utils
def test_success():
    """Test success message output."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger.success("Success message")

        mock_console.assert_called_once_with("Success message", color="green")


@pytest.mark.utils
def test_print_tool_header():
    """Test tool header printing."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger.print_tool_header("ruff", "check")

        # Should make multiple console_output calls for border, header, etc.
        assert mock_console.call_count >= 4

        # Check that the header contains the tool name and action
        calls = [str(call) for call in mock_console.call_args_list]
        header_content = "".join(calls)
        assert "ruff" in header_content
        assert "check" in header_content
        assert "🦀" in header_content  # ruff emoji


@pytest.mark.utils
def test_print_tool_result_with_output():
    """Test printing tool results when there is output."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger.print_tool_result("ruff", "Some tool output", 5)

        # Should output the content and error message
        calls = [str(call) for call in mock_console.call_args_list]
        output_content = "".join(calls)
        assert "Some tool output" in output_content
        assert "Found 5 issues" in output_content


@pytest.mark.utils
def test_print_tool_result_no_issues():
    """Test printing tool results when there are no issues."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "success") as mock_success:
            logger.print_tool_result("ruff", "", 0)

        mock_success.assert_called_once_with("✓ No issues found.")


@pytest.mark.utils
def test_print_execution_summary():
    """Test printing execution summary."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        # Mock tool results
        mock_result1 = MagicMock()
        mock_result1.name = "ruff"
        mock_result1.issues_count = 0

        mock_result2 = MagicMock()
        mock_result2.name = "yamllint"
        mock_result2.issues_count = 2

        tool_results = [mock_result1, mock_result2]

        with patch.object(logger, "console_output"):
            with patch.object(logger, "_print_summary_table") as mock_table:
                with patch.object(logger, "_print_final_status") as mock_status:
                    with patch.object(logger, "_print_ascii_art") as mock_art:
                        logger.print_execution_summary("check", tool_results)

        # Verify all components were called
        mock_table.assert_called_once_with("check", tool_results)
        mock_status.assert_called_once_with("check", 2)  # total issues
        mock_art.assert_called_once_with(2)


@pytest.mark.utils
def test_save_console_log():
    """Test saving console log to file."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        # Add some console messages
        logger.console_messages = ["Message 1", "Message 2"]

        logger.save_console_log()

        # Check that file was created and contains messages
        console_log_path = run_dir / "console.log"
        assert console_log_path.exists()

        content = console_log_path.read_text()
        assert "Message 1" in content
        assert "Message 2" in content


@pytest.mark.utils
def test_print_final_status_format_no_issues():
    """Test final status for format operation with no issues."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger._print_final_status("fmt", 0)

        calls = [str(call) for call in mock_console.call_args_list]
        output = "".join(calls)
        assert "No issues found" in output


@pytest.mark.utils
def test_print_final_status_format_with_fixes():
    """Test final status for format operation with fixes."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger._print_final_status("fmt", 3)

        calls = [str(call) for call in mock_console.call_args_list]
        output = "".join(calls)
        assert "Fixed 3 issues" in output


@pytest.mark.utils
def test_print_final_status_check_with_issues():
    """Test final status for check operation with issues."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch.object(logger, "console_output") as mock_console:
            logger._print_final_status("check", 5)

        calls = [str(call) for call in mock_console.call_args_list]
        output = "".join(calls)
        assert "TOTAL ISSUES: 5" in output


@pytest.mark.utils
def test_print_ascii_art_success():
    """Test printing ASCII art for success case."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch("lintro.utils.console_logger.read_ascii_art") as mock_read:
            mock_read.return_value = ["ASCII", "ART", "SUCCESS"]
            with patch.object(logger, "console_output") as mock_console:
                logger._print_ascii_art(0)  # 0 issues = success

        mock_read.assert_called_once_with("success.txt")
        mock_console.assert_called_once_with("ASCII\nART\nSUCCESS")


@pytest.mark.utils
def test_print_ascii_art_failure():
    """Test printing ASCII art for failure case."""
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        logger = SimpleLintroLogger(run_dir=run_dir)

        with patch("lintro.utils.console_logger.read_ascii_art") as mock_read:
            mock_read.return_value = ["ASCII", "ART", "FAIL"]
            with patch.object(logger, "console_output") as mock_console:
                logger._print_ascii_art(5)  # 5 issues = failure

        mock_read.assert_called_once_with("fail.txt")
        mock_console.assert_called_once_with("ASCII\nART\nFAIL")
