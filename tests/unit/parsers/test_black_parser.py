"""Tests for Black parser utilities."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.black.black_parser import parse_black_output


def test_parse_black_output_would_reformat_single_file() -> None:
    """Parse a single-file 'would reformat' message into one issue."""
    output = (
        "would reformat src/app.py\nAll done! 💥 💔 💥\n1 file would be reformatted."
    )
    issues = parse_black_output(output)
    assert_that(issues).is_length(1)
    assert_that(issues[0].file).ends_with("src/app.py")
    assert_that(issues[0].message).contains("Would reformat")


def test_parse_black_output_reformatted_multiple_files() -> None:
    """Parse multi-file 'reformatted' output into per-file issues."""
    output = (
        "reformatted a.py\nreformatted b.py\nAll done! ✨ 🍰 ✨\n2 files reformatted"
    )
    issues = parse_black_output(output)
    files = {i.file for i in issues}
    assert_that(files).is_equal_to({"a.py", "b.py"})
    assert_that(all("Reformatted" in i.message for i in issues)).is_true()


def test_parse_black_output_no_issues() -> None:
    """Return empty list when Black reports no issues."""
    output = "All done! ✨ 🍰 ✨\n1 file left unchanged."
    issues = parse_black_output(output)
    assert_that(issues).is_equal_to([])
