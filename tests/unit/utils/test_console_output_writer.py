"""Unit tests for ConsoleOutputWriter class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.console_output_writer import ConsoleOutputWriter


@pytest.fixture
def writer() -> ConsoleOutputWriter:
    """Create a ConsoleOutputWriter instance for testing.

    Returns:
        ConsoleOutputWriter instance for testing.
    """
    return ConsoleOutputWriter()


def test_initialization(writer: ConsoleOutputWriter) -> None:
    """Test that writer initializes with empty messages list.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    assert_that(writer.console_messages).is_empty()


def test_console_output_no_color(writer: ConsoleOutputWriter) -> None:
    """Test console_output without color.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with patch("lintro.utils.console_output_writer.click.echo") as mock_echo:
        writer.console_output("Test message")

        mock_echo.assert_called_once_with("Test message")
        assert_that(writer.console_messages).contains("Test message")


def test_console_output_with_color(writer: ConsoleOutputWriter) -> None:
    """Test console_output with color.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo") as mock_echo,
        patch("lintro.utils.console_output_writer.click.style") as mock_style,
    ):
        mock_style.return_value = "styled text"
        writer.console_output("Test message", color="green")

        mock_style.assert_called_once_with("Test message", fg="green")
        mock_echo.assert_called_once_with("styled text")
        assert_that(writer.console_messages).contains("Test message")


def test_info(writer: ConsoleOutputWriter) -> None:
    """Test info method logs message.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo") as mock_echo,
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        writer.info("Info message")

        mock_echo.assert_called_once_with("Info message")
        mock_logger.info.assert_called_once()
        assert_that(writer.console_messages).contains("Info message")


def test_info_blue(writer: ConsoleOutputWriter) -> None:
    """Test info_blue method logs in cyan bold.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo") as mock_echo,
        patch("lintro.utils.console_output_writer.click.style") as mock_style,
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        mock_style.return_value = "styled"
        writer.info_blue("Blue message")

        mock_style.assert_called_once_with("Blue message", fg="cyan", bold=True)
        mock_echo.assert_called_once_with("styled")
        mock_logger.info.assert_called_once()
        assert_that(writer.console_messages).contains("Blue message")


def test_success(writer: ConsoleOutputWriter) -> None:
    """Test success method logs in green.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo"),
        patch("lintro.utils.console_output_writer.click.style") as mock_style,
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        mock_style.return_value = "styled"
        writer.success("Success message")

        mock_style.assert_called_once_with("Success message", fg="green")
        mock_logger.info.assert_called_once()
        assert_that(writer.console_messages).contains("Success message")


def test_warning(writer: ConsoleOutputWriter) -> None:
    """Test warning method prefixes with WARNING.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo"),
        patch("lintro.utils.console_output_writer.click.style") as mock_style,
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        mock_style.return_value = "styled"
        writer.warning("Warning message")

        mock_style.assert_called_once_with("WARNING: Warning message", fg="yellow")
        mock_logger.warning.assert_called_once()
        assert_that(writer.console_messages).contains("WARNING: Warning message")


def test_error(writer: ConsoleOutputWriter) -> None:
    """Test error method prefixes with ERROR.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo"),
        patch("lintro.utils.console_output_writer.click.style") as mock_style,
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        mock_style.return_value = "styled"
        writer.error("Error message")

        mock_style.assert_called_once_with("ERROR: Error message", fg="red", bold=True)
        mock_logger.error.assert_called_once()
        assert_that(writer.console_messages).contains("ERROR: Error message")


def test_save_console_log(writer: ConsoleOutputWriter, tmp_path: Path) -> None:
    """Test saving console messages to file.

    Args:
        writer: ConsoleOutputWriter instance for testing.
        tmp_path: Temporary directory path for testing.
    """
    writer.console_messages = ["Message 1", "Message 2", "Message 3"]

    with patch("lintro.utils.console_output_writer.logger"):
        writer.save_console_log(tmp_path)

    log_path = tmp_path / "console.log"
    assert_that(log_path.exists()).is_true()
    content = log_path.read_text()
    assert_that(content).contains("Message 1")
    assert_that(content).contains("Message 2")
    assert_that(content).contains("Message 3")


def test_save_console_log_handles_error(writer: ConsoleOutputWriter) -> None:
    """Test save_console_log handles write errors gracefully.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    writer.console_messages = ["Message"]

    with (
        patch("builtins.open", side_effect=OSError("Permission denied")),
        patch("lintro.utils.console_output_writer.logger") as mock_logger,
    ):
        writer.save_console_log("/invalid/path")
        mock_logger.error.assert_called_once()


def test_multiple_messages_tracked(writer: ConsoleOutputWriter) -> None:
    """Test that multiple messages are tracked in order.

    Args:
        writer: ConsoleOutputWriter instance for testing.
    """
    with (
        patch("lintro.utils.console_output_writer.click.echo"),
        patch("lintro.utils.console_output_writer.click.style", return_value="s"),
        patch("lintro.utils.console_output_writer.logger"),
    ):
        writer.info("First")
        writer.success("Second")
        writer.warning("Third")
        writer.error("Fourth")

        assert_that(len(writer.console_messages)).is_equal_to(4)
        assert_that(writer.console_messages[0]).is_equal_to("First")
        assert_that(writer.console_messages[1]).is_equal_to("Second")
        assert_that(writer.console_messages[2]).is_equal_to("WARNING: Third")
        assert_that(writer.console_messages[3]).is_equal_to("ERROR: Fourth")
