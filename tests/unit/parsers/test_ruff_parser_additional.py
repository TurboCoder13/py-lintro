"""Additional tests for Ruff parser coverage gaps."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.ruff.ruff_parser import parse_ruff_output


def test_parse_ruff_output_plain_json_array() -> None:
    """Parse a simple JSON array output into issues list."""
    output = (
        "[\n"
        '  {"filename": "a.py", "location": {"row": 1, "column": 2},'
        '   "code": "E1", "message": "x"}\n'
        "]"
    )
    issues = parse_ruff_output(output)
    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].file.endswith("a.py")).is_true()


def test_parse_ruff_output_empty_and_malformed_line_skipped() -> None:
    """Skip empty and malformed lines in JSONL output gracefully."""
    jl = (
        "\n\n"  # empties ignored
        '{"filename":"b.py","location":{"row":2,"column":1},"code":"F","message":"m"}\n'
        "not-json\n"  # malformed line skipped
    )
    issues = parse_ruff_output(jl)
    files = [i.file for i in issues]
    assert_that(files).contains("b.py")
