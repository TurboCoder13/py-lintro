"""Unit tests for ASCII art normalization helpers."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.formatting import normalize_ascii_block, normalize_ascii_file_sections


def test_normalize_ascii_block_center_and_alignments():
    """Normalize ASCII blocks across horizontal/vertical alignments."""
    src = ["XX", "XXXX", "X"]
    out = normalize_ascii_block(
        src,
        width=10,
        height=5,
        align="center",
        valign="middle",
    )
    assert_that(len(out)).is_equal_to(5)
    assert_that(all(len(line) == 10 for line in out)).is_true()
    assert_that({"XX", "XXXX", "X"}).contains(out[2].strip())
    left = normalize_ascii_block(["X"], width=5, height=1, align="left")
    right = normalize_ascii_block(["X"], width=5, height=1, align="right")
    assert_that(left[0].startswith("X") and left[0].endswith("   ")).is_true()
    assert_that(right[0].startswith("    ") and right[0].endswith("X")).is_true()


def test_normalize_ascii_file_sections(tmp_path: Path):
    """Normalize sections from a file and enforce width/height constraints.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    p = tmp_path / "art.txt"
    p.write_text("A\nAA\n\nBBB\nB\n", encoding="utf-8")
    sections = normalize_ascii_file_sections(p, width=6, height=3)
    assert_that(len(sections)).is_equal_to(2)
    for sec in sections:
        assert_that(len(sec)).is_equal_to(3)
        assert_that(all(len(line) == 6 for line in sec)).is_true()
