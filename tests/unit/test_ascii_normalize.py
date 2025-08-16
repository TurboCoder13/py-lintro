from __future__ import annotations

from pathlib import Path

from lintro.utils.formatting import (
    normalize_ascii_block,
    normalize_ascii_file_sections,
)


def test_normalize_ascii_block_center_and_alignments():
    src = [
        "XX",
        "XXXX",
        "X",
    ]
    out = normalize_ascii_block(
        src, width=10, height=5, align="center", valign="middle"
    )
    assert len(out) == 5
    assert all(len(line) == 10 for line in out)
    # Centered line should have spaces on both sides
    assert out[2].strip() in {"XX", "XXXX", "X"}

    left = normalize_ascii_block(["X"], width=5, height=1, align="left")
    right = normalize_ascii_block(["X"], width=5, height=1, align="right")
    assert left[0].startswith("X") and left[0].endswith("   ")
    assert right[0].startswith("    ") and right[0].endswith("X")


def test_normalize_ascii_file_sections(tmp_path: Path):
    p = tmp_path / "art.txt"
    p.write_text("A\nAA\n\nBBB\nB\n", encoding="utf-8")
    sections = normalize_ascii_file_sections(p, width=6, height=3)
    assert len(sections) == 2
    for sec in sections:
        assert len(sec) == 3
        assert all(len(line) == 6 for line in sec)
