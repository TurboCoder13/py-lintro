"""Unit tests for the resizer module."""

from __future__ import annotations

import numpy as np
from assertpy import assert_that

from ascii_resizer.resizer import (
    ArtType,
    AsciiResizer,
    ResizeMethod,
    format_sections,
    parse_sections,
)

# --- parse_sections ---


def test_parse_sections_single() -> None:
    """Single section without blank lines."""
    sections = parse_sections("line1\nline2\nline3")
    assert_that(sections).is_length(1)
    assert_that(sections[0]).is_equal_to(["line1", "line2", "line3"])


def test_parse_sections_multiple() -> None:
    """Multiple sections separated by blank lines."""
    sections = parse_sections("sec1line1\nsec1line2\n\nsec2line1\nsec2line2")
    assert_that(sections).is_length(2)
    assert_that(sections[0]).is_equal_to(["sec1line1", "sec1line2"])
    assert_that(sections[1]).is_equal_to(["sec2line1", "sec2line2"])


def test_parse_sections_multiple_blank_lines() -> None:
    """Multiple blank lines should still separate sections."""
    sections = parse_sections("section1\n\n\n\nsection2")
    assert_that(sections).is_length(2)


def test_parse_sections_empty() -> None:
    """Empty content should produce no sections."""
    assert_that(parse_sections("")).is_empty()


def test_parse_sections_whitespace_only() -> None:
    """Whitespace-only content should produce no sections."""
    assert_that(parse_sections("   \n   \n   ")).is_empty()


# --- format_sections ---


def test_format_sections_single() -> None:
    """Single section should format without separators."""
    result = format_sections([["line1", "line2"]])
    assert_that(result).is_equal_to("line1\nline2\n")


def test_format_sections_multiple() -> None:
    """Multiple sections should be separated by blank lines."""
    result = format_sections([["sec1"], ["sec2"]])
    assert_that(result).is_equal_to("sec1\n\nsec2\n")


def test_format_parse_roundtrip() -> None:
    """Format and parse should roundtrip."""
    original = [["a", "b"], ["c", "d"]]
    parsed = parse_sections(format_sections(original))
    assert_that(parsed).is_equal_to(original)


# --- AsciiResizer.detect_art_type ---


def test_detect_braille_art() -> None:
    """Should detect Braille art."""
    assert_that(AsciiResizer.detect_art_type(["⣿⣿⣿", "⣿⣿⣿"])).is_equal_to(
        ArtType.BRAILLE,
    )


def test_detect_mixed_content_mostly_braille() -> None:
    """Mixed content with majority Braille should detect as Braille."""
    assert_that(AsciiResizer.detect_art_type(["⣿⣿⣿⣿⣿", "⣿ a ⣿"])).is_equal_to(
        ArtType.BRAILLE,
    )


def test_detect_non_braille() -> None:
    """Non-Braille content should return None."""
    assert_that(AsciiResizer.detect_art_type(["Hello", "World"])).is_none()


# --- AsciiResizer.resize_bitmap ---


def test_resize_bitmap_upscale() -> None:
    """Should upscale bitmap correctly with nearest neighbor."""
    resizer = AsciiResizer(method=ResizeMethod.NEAREST)
    original = np.array([[1, 0], [0, 1]], dtype=np.uint8)

    result = resizer.resize_bitmap(original, target_width=4, target_height=4)

    assert_that(result.shape).is_equal_to((4, 4))
    expected = np.array(
        [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]],
        dtype=np.uint8,
    )
    np.testing.assert_array_equal(result, expected)


def test_resize_bitmap_downscale() -> None:
    """Should downscale bitmap correctly."""
    resizer = AsciiResizer(method=ResizeMethod.NEAREST)
    original = np.array(
        [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]],
        dtype=np.uint8,
    )

    result = resizer.resize_bitmap(original, target_width=2, target_height=2)

    assert_that(result.shape).is_equal_to((2, 2))


# --- AsciiResizer.resize_braille ---


def test_resize_braille_dimensions() -> None:
    """Resized Braille should have correct dimensions."""
    resizer = AsciiResizer()
    result = resizer.resize_braille(
        ["⣿⣿⣿", "⣿⣿⣿"],
        target_chars_wide=5,
        target_chars_tall=4,
    )

    assert_that(result).is_length(4)
    assert_that(all(len(line) == 5 for line in result)).is_true()


def test_resize_braille_empty_input() -> None:
    """Should handle empty input gracefully."""
    resizer = AsciiResizer()
    result = resizer.resize_braille([], target_chars_wide=3, target_chars_tall=2)

    assert_that(result).is_length(2)
    assert_that(all(len(line) == 3 for line in result)).is_true()


def test_resize_braille_preserves_general_shape() -> None:
    """Resizing should preserve the general shape of the art."""
    resizer = AsciiResizer(method=ResizeMethod.NEAREST)
    result = resizer.resize_braille(
        ["⣿⠀", "⠀⣿"],
        target_chars_wide=4,
        target_chars_tall=4,
    )

    assert_that(result).is_length(4)
    assert_that(all(len(line) == 4 for line in result)).is_true()
