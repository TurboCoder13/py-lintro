from __future__ import annotations

from lintro.parsers.black.black_parser import parse_black_output


def test_parse_black_output_would_reformat_single_file():
    output = (
        "would reformat src/app.py\nAll done! 💥 💔 💥\n1 file would be reformatted."
    )
    issues = parse_black_output(output)
    assert len(issues) == 1
    assert issues[0].file.endswith("src/app.py")
    assert "Would reformat" in issues[0].message


def test_parse_black_output_reformatted_multiple_files():
    output = (
        "reformatted a.py\nreformatted b.py\nAll done! ✨ 🍰 ✨\n2 files reformatted"
    )
    issues = parse_black_output(output)
    files = {i.file for i in issues}
    assert files == {"a.py", "b.py"}
    assert all("Reformatted" in i.message for i in issues)


def test_parse_black_output_no_issues():
    output = "All done! ✨ 🍰 ✨\n1 file left unchanged."
    issues = parse_black_output(output)
    assert issues == []
