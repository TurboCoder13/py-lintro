"""Console output writer utilities for Lintro.

Handles all console display operations, separating them from logging concerns.
"""

from pathlib import Path
from typing import Any

import click
from loguru import logger


class ConsoleOutputWriter:
    """Handles console output operations for Lintro.

    This class separates console display logic from logging, following
    the Single Responsibility Principle.
    """

    def __init__(self) -> None:
        """Initialize the console output writer."""
        self.console_messages: list[str] = []

    def console_output(
        self,
        text: str,
        color: str | None = None,
    ) -> None:
        """Display text on console and track for console.log.

        Args:
            text: str: Text to display.
            color: str | None: Optional color for the text.
        """
        if color:
            click.echo(click.style(text, fg=color))
        else:
            click.echo(text)

        # Track for console.log (without color codes)
        self.console_messages.append(text)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for logger formatting.
        """
        click.echo(message)
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def info_blue(self, message: str, **kwargs: Any) -> None:
        """Log an info message to the console in blue color.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for formatting.
        """
        styled_message = click.style(message, fg="cyan", bold=True)
        click.echo(styled_message)
        self.console_messages.append(message)
        logger.info(message, **kwargs)

    def success(self, message: str, **kwargs: Any) -> None:
        """Log a success message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for logger formatting.
        """
        self.console_output(text=message, color="green")
        logger.info(f"SUCCESS: {message}", **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for logger formatting.
        """
        warning_text = f"WARNING: {message}"
        click.echo(click.style(warning_text, fg="yellow"))
        # Store the full warning text for consistency with console output
        self.console_messages.append(warning_text)
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message to the console.

        Args:
            message: str: The message to log.
            **kwargs: Additional keyword arguments for logger formatting.
        """
        error_text = f"ERROR: {message}"
        click.echo(click.style(error_text, fg="red", bold=True))
        # Store the full error text for consistency with console output
        self.console_messages.append(error_text)
        logger.error(message, **kwargs)

    def save_console_log(self, run_dir: str | Path) -> None:
        """Save tracked console messages to console.log.

        Args:
            run_dir: str | Path: Directory to save the console log.
        """
        console_log_path = Path(run_dir) / "console.log"
        try:
            with open(console_log_path, "w", encoding="utf-8") as f:
                for message in self.console_messages:
                    f.write(f"{message}\n")
            logger.debug(f"Saved console output to {console_log_path}")
        except OSError as e:
            logger.error(f"Failed to save console log to {console_log_path}: {e}")
