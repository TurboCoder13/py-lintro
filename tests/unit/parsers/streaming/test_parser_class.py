"""Tests for StreamingParser class."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.base_issue import BaseIssue
from lintro.parsers.streaming import StreamingParser
from tests.unit.parsers.streaming.conftest import SimpleIssue


def test_stream_json_lines_uses_parse_item() -> None:
    """StreamingParser.stream_json_lines uses parse_item method."""

    class TestParser(StreamingParser):
        def parse_item(self, item: dict[str, object]) -> BaseIssue | None:
            file_val = item.get("file")
            return SimpleIssue(
                file=str(file_val) if file_val else "",
            )

    parser = TestParser("test")
    output = '{"file": "a.py"}\n{"file": "b.py"}\n'
    results: list[BaseIssue] = list(parser.stream_json_lines(output))

    assert_that(results).is_length(2)


def test_stream_text_lines_uses_parse_line() -> None:
    """StreamingParser.stream_text_lines uses parse_line method."""

    class TestParser(StreamingParser):
        def parse_line(self, line: str) -> BaseIssue | None:
            if line.startswith("E:"):
                return SimpleIssue(message=line[2:].strip())
            return None

    parser = TestParser("test")
    output = "I: info\nE: error\nI: more\n"
    results: list[BaseIssue] = list(parser.stream_text_lines(output))

    assert_that(results).is_length(1)
    assert_that(results[0].message).is_equal_to("error")


def test_stream_json_array_uses_parse_item() -> None:
    """StreamingParser.stream_json_array uses parse_item method."""

    class TestParser(StreamingParser):
        def parse_item(self, item: dict[str, object]) -> BaseIssue | None:
            file_val = item.get("file")
            return SimpleIssue(
                file=str(file_val) if file_val else "",
            )

    parser = TestParser("test")
    output = '[{"file": "a.py"}]'
    results: list[BaseIssue] = list(parser.stream_json_array(output))

    assert_that(results).is_length(1)


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("parse_item", ({},)),
        ("parse_line", ("test",)),
    ],
)
def test_methods_raise_not_implemented(
    method: str,
    args: tuple[object, ...],
) -> None:
    """parse_item and parse_line raise NotImplementedError by default.

    Args:
        method: The method name to test.
        args: Arguments to pass to the method.
    """
    parser = StreamingParser("test")

    with pytest.raises(NotImplementedError):
        getattr(parser, method)(*args)
