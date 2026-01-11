"""Streaming parser utilities for incremental output processing.

This module provides generator-based parsing for tool output that can yield
issues as they are parsed, rather than buffering the entire output first.

Supports:
- JSON Lines: Each line is a complete JSON object (naturally streamable)
- Line-based text: Each line can be parsed independently
- JSON arrays: Requires buffering but provides consistent interface

Usage:
    # Stream JSON Lines output
    for issue in stream_json_lines(output, parse_func):
        process(issue)

    # Stream text output
    for issue in stream_text_lines(output, parse_line_func):
        process(issue)
"""

from __future__ import annotations

import json
from collections.abc import Callable, Generator, Iterable
from typing import TypeVar

from loguru import logger

from lintro.parsers.base_issue import BaseIssue

IssueT = TypeVar("IssueT", bound=BaseIssue)


def stream_json_lines(
    output: str | Iterable[str],
    parse_item: Callable[[dict[str, object]], IssueT | None],
    tool_name: str = "tool",
) -> Generator[IssueT, None, None]:
    r"""Stream JSON Lines output, yielding parsed issues incrementally.

    JSON Lines format has one JSON object per line, making it naturally
    streamable. Each line is parsed independently as soon as it's received.

    Args:
        output: Either a string containing newline-separated JSON objects,
            or an iterable of lines (e.g., from subprocess stdout).
        parse_item: Function that parses a single JSON object dict into an
            issue. Should return None for items that should be skipped.
        tool_name: Name of the tool for logging purposes.

    Yields:
        Parsed issue objects as they are processed.

    Examples:
        >>> def parse(item):
        ...     return MyIssue(file=item.get("file", ""))
        >>> output = '{"file": "a.py"}\\n{"file": "b.py"}\\n'
        >>> list(stream_json_lines(output, parse))  # doctest: +SKIP
        [MyIssue(file='a.py'), MyIssue(file='b.py')]
    """
    lines: Iterable[str]
    lines = output.splitlines() if isinstance(output, str) else output

    for line in lines:
        line_str = line.strip() if isinstance(line, str) else str(line).strip()

        if not line_str:
            continue

        # Skip lines that don't look like JSON objects
        if not line_str.startswith("{"):
            continue

        try:
            item = json.loads(line_str)
            if not isinstance(item, dict):
                logger.debug(f"Skipping non-dict JSON in {tool_name}: {type(item)}")
                continue

            parsed = parse_item(item)
            if parsed is not None:
                yield parsed

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse {tool_name} JSON line: {e}")
            continue
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Failed to parse {tool_name} item: {e}")
            continue


def stream_text_lines(
    output: str | Iterable[str],
    parse_line: Callable[[str], IssueT | None],
    strip_ansi: bool = True,
) -> Generator[IssueT, None, None]:
    r"""Stream text output, parsing each line independently.

    For tools that output one issue per line in a text format, this allows
    processing each line as soon as it's received.

    Args:
        output: Either a string containing newlines, or an iterable of lines.
        parse_line: Function that parses a single line into an issue.
            Should return None for lines that don't contain issues.
        strip_ansi: Whether to strip ANSI escape codes before parsing.

    Yields:
        Parsed issue objects as they are processed.

    Examples:
        >>> def parse(line):
        ...     if "error" in line:
        ...         return MyIssue(message=line)
        ...     return None
        >>> output = "info: ok\\nerror: bad\\n"
        >>> list(stream_text_lines(output, parse))  # doctest: +SKIP
        [MyIssue(message='error: bad')]
    """
    from lintro.parsers.base_parser import strip_ansi_codes

    lines: Iterable[str]
    lines = output.splitlines() if isinstance(output, str) else output

    for line in lines:
        line_str = line if isinstance(line, str) else str(line)

        if strip_ansi:
            line_str = strip_ansi_codes(line_str)

        line_str = line_str.rstrip()
        if not line_str:
            continue

        try:
            parsed = parse_line(line_str)
            if parsed is not None:
                yield parsed
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Failed to parse line: {e}")
            continue


def stream_json_array_fallback(
    output: str,
    parse_item: Callable[[dict[str, object]], IssueT | None],
    tool_name: str = "tool",
) -> Generator[IssueT, None, None]:
    """Parse a JSON array and yield items incrementally.

    For tools that output a JSON array (not JSON Lines), this function
    parses the full array but still yields items one at a time for
    consistent streaming interface.

    Falls back to JSON Lines parsing if array parsing fails.

    Args:
        output: String containing a JSON array or JSON Lines.
        parse_item: Function that parses a single JSON object dict into an
            issue. Should return None for items that should be skipped.
        tool_name: Name of the tool for logging purposes.

    Yields:
        Parsed issue objects.
    """
    if not output or output.strip() in ("[]", "{}"):
        return

    # Try JSON array first
    try:
        # Handle possible trailing non-JSON data
        json_end = output.rfind("]")
        if json_end != -1:
            json_part = output[: json_end + 1]
            data = json.loads(json_part)
        else:
            data = json.loads(output)

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    logger.debug(f"Skipping non-dict item in {tool_name}")
                    continue
                try:
                    parsed = parse_item(item)
                    if parsed is not None:
                        yield parsed
                except (KeyError, TypeError, ValueError) as e:
                    logger.debug(f"Failed to parse {tool_name} item: {e}")
                    continue
            return

    except json.JSONDecodeError:
        logger.debug(f"{tool_name} array parsing failed, trying JSON Lines")

    # Fallback to JSON Lines
    yield from stream_json_lines(output, parse_item, tool_name)


class StreamingParser:
    """Base class for creating streaming parsers.

    Subclasses implement the parse_item or parse_line method to define
    how individual items/lines are converted to issues.

    Attributes:
        tool_name: Name of the tool for logging.

    Examples:
        >>> class MyStreamingParser(StreamingParser):
        ...     def parse_item(self, item):
        ...         return MyIssue(file=item.get("file", ""))
        >>> parser = MyStreamingParser("mytool")
        >>> for issue in parser.stream_json_lines(output):
        ...     print(issue)
    """

    def __init__(self, tool_name: str = "tool") -> None:
        """Initialize streaming parser.

        Args:
            tool_name: Name of the tool for logging purposes.
        """
        self.tool_name = tool_name

    def parse_item(self, item: dict[str, object]) -> BaseIssue | None:
        """Parse a single JSON item into an issue.

        Override this method in subclasses to implement JSON parsing.

        Args:
            item: Dictionary from JSON parsing.

        Raises:
            NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement parse_item")

    def parse_line(self, line: str) -> BaseIssue | None:
        """Parse a single text line into an issue.

        Override this method in subclasses to implement text parsing.

        Args:
            line: Text line to parse.

        Raises:
            NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement parse_line")

    def stream_json_lines(
        self,
        output: str | Iterable[str],
    ) -> Generator[BaseIssue, None, None]:
        """Stream JSON Lines output using this parser's parse_item method.

        Args:
            output: String or iterable of lines to parse.

        Yields:
            Parsed issues.
        """
        yield from stream_json_lines(output, self.parse_item, self.tool_name)

    def stream_text_lines(
        self,
        output: str | Iterable[str],
        strip_ansi: bool = True,
    ) -> Generator[BaseIssue, None, None]:
        """Stream text output using this parser's parse_line method.

        Args:
            output: String or iterable of lines to parse.
            strip_ansi: Whether to strip ANSI codes.

        Yields:
            Parsed issues.
        """
        yield from stream_text_lines(output, self.parse_line, strip_ansi)

    def stream_json_array(
        self,
        output: str,
    ) -> Generator[BaseIssue, None, None]:
        """Stream JSON array with fallback to JSON Lines.

        Args:
            output: String containing JSON array or JSON Lines.

        Yields:
            Parsed issues.
        """
        yield from stream_json_array_fallback(output, self.parse_item, self.tool_name)


def collect_streaming_results(
    generator: Generator[IssueT, None, None],
) -> list[IssueT]:
    """Collect all results from a streaming parser into a list.

    Utility function to convert streaming parser output to the traditional
    list-based interface used by existing code.

    Args:
        generator: Generator yielding parsed issues.

    Returns:
        List of all parsed issues.

    Examples:
        >>> results = collect_streaming_results(parser.stream_json_lines(output))
    """
    return list(generator)
