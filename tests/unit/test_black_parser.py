"""Tests for Black parser utilities."""

from __future__ import annotations

from lintro.parsers.black.black_parser import parse_black_output


def test_parse_black_output_would_reformat_single_file() -> None:
    """Parse a single-file 'would reformat' message into one issue."""
    output = (
        "would reformat src/app.py\nAll done! 💥 💔 💥\n1 file would be reformatted."
    )
    issues = parse_black_output(output)
    assert len(issues) == 1
    assert issues[0].file.endswith("src/app.py")
    assert "Would reformat" in issues[0].message


def test_parse_black_output_reformatted_multiple_files() -> None:
    """Parse multi-file 'reformatted' output into per-file issues."""
    output = (
        "reformatted a.py\nreformatted b.py\nAll done! ✨ 🍰 ✨\n2 files reformatted"
    )
    issues = parse_black_output(output)
    files = {i.file for i in issues}
    assert files == {"a.py", "b.py"}
    assert all("Reformatted" in i.message for i in issues)


def test_parse_black_output_no_issues() -> None:
    """Return empty list when Black reports no issues."""
    output = "All done! ✨ 🍰 ✨\n1 file left unchanged."
    issues = parse_black_output(output)
    assert issues == []
