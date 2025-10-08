"""Additional unit tests for Ruff parser variants and format check output."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.ruff.ruff_parser import (
    parse_ruff_format_check_output,
    parse_ruff_output,
)


def test_parse_ruff_output_json_lines_and_variants():
    """Parse JSON lines with variant keys and fix metadata."""
    # Mixed JSON lines with different location key variants and fix metadata
    jl = (
        '{"filename":"a.py","location":{"row":1,"column":2},'
        '"end_location":{"row":1,"column":10},"code":"E501",'
        '"message":"long line"}\n'
        '{"file":"b.py","start":{"line":3,"col":1},'
        '"end":{"line":3,"col":5},"rule":"F401","message":"unused"}\n'
        '{"filename":"c.py","location":{"row":5,"column":4},'
        '"code":"E702","message":"semicolon"}'
    )
    issues = parse_ruff_output(jl)
    files = [i.file for i in issues]
    codes = [i.code for i in issues]
    assert_that(files).contains("a.py", "b.py", "c.py")
    assert_that(codes).contains("E501", "F401", "E702")


def test_parse_ruff_output_trailing_non_json():
    """Ignore trailing non-JSON content after a JSON array."""
    # Parser should ignore trailing non-JSON after array
    output = (
        "[\n"
        '  {"filename": "x.py", "location": {"row": 1, "column": 1}, '
        '"code": "F401", "message": "unused"}\n'
        "]\n"
        "Ruff 0.4.0 summary...\n"
    )
    issues = parse_ruff_output(output)
    assert len(issues) == 1
    assert issues[0].file.endswith("x.py")


def test_parse_ruff_format_check_output_various_lines():
    """Extract files from various format-check output lines."""
    out = (
        "Would reformat: src/app.py\n"
        "Some other text\n"
        "Would reformat tests/test_app.py\n"
        "Summary: 2 files would be reformatted\n"
    )
    files = parse_ruff_format_check_output(out)
    assert_that(files).contains("src/app.py", "tests/test_app.py")


def test_parse_ruff_format_check_output_variants_more():
    """Support alternate wording for 'Would reformat' lines."""
    out = "Would reformat: a.py\nWould reformat b.py\n"
    files = parse_ruff_format_check_output(out)
    assert_that(sorted(files)).is_equal_to(["a.py", "b.py"])
