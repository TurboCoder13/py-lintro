"""Shared fixtures for unit tests."""

import pytest


class FakeLogger:
    """Minimal logger stub capturing method calls for assertions."""

    def __init__(self) -> None:
        """Initialize the fake logger with call storage and run dir."""
        self.calls: list[tuple[str, tuple, dict]] = []
        self.run_dir = ".lintro/test"

    def _rec(self, name: str, *a, **k) -> None:
        self.calls.append((name, a, k))

    def info(self, *a, **k) -> None:
        """Record an info call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("info", *a, **k)

    def debug(self, *a, **k) -> None:
        """Record a debug call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("debug", *a, **k)

    def warning(self, *a, **k) -> None:
        """Record a warning call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("warning", *a, **k)

    def error(self, *a, **k) -> None:
        """Record an error call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("error", *a, **k)

    def success(self, *a, **k) -> None:
        """Record a success call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("success", *a, **k)

    def console_output(self, *a, **k) -> None:
        """Record console output.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("console_output", *a, **k)

    def print_lintro_header(self, *a, **k) -> None:
        """Record header printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_lintro_header", *a, **k)

    def print_verbose_info(self, *a, **k) -> None:
        """Record verbose info printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_verbose_info", *a, **k)

    def print_tool_header(self, *a, **k) -> None:
        """Record tool header printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_tool_header", *a, **k)

    def print_tool_result(self, *a, **k) -> None:
        """Record tool result printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_tool_result", *a, **k)

    def print_execution_summary(self, *a, **k) -> None:
        """Record execution summary printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_execution_summary", *a, **k)

    def print_post_checks_header(self, *a, **k) -> None:
        """Record post checks header printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_post_checks_header", *a, **k)

    def save_console_log(self, *a, **k) -> None:
        """Record console log saving.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("save_console_log", *a, **k)


@pytest.fixture
def fake_logger():
    """Provide a FakeLogger instance for testing.

    Returns:
        FakeLogger: Configured FakeLogger instance for unit testing.
    """
    return FakeLogger()
