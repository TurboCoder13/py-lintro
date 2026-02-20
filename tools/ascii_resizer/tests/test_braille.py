"""Unit tests for Braille encoding/decoding."""

from __future__ import annotations

import numpy as np
from assertpy import assert_that

from ascii_resizer import braille


def test_is_braille_valid() -> None:
    """Braille characters should be detected."""
    assert_that(braille.is_braille("⠀")).is_true()  # U+2800
    assert_that(braille.is_braille("⣿")).is_true()  # U+28FF
    assert_that(braille.is_braille("⠃")).is_true()


def test_is_braille_invalid() -> None:
    """Non-Braille characters should not be detected."""
    assert_that(braille.is_braille("A")).is_false()
    assert_that(braille.is_braille(" ")).is_false()
    assert_that(braille.is_braille("█")).is_false()
    assert_that(braille.is_braille("")).is_false()
    assert_that(braille.is_braille("⠀⠀")).is_false()  # Multi-char


def test_char_to_dots_empty() -> None:
    """Empty braille character should have 0 dots."""
    assert_that(braille.char_to_dots("⠀")).is_equal_to(0)


def test_char_to_dots_full() -> None:
    """Full braille character should have all dots (255)."""
    assert_that(braille.char_to_dots("⣿")).is_equal_to(255)


def test_char_to_dots_specific() -> None:
    """Specific dot patterns should decode correctly."""
    assert_that(braille.char_to_dots("⠁")).is_equal_to(0x01)  # Dot 1
    assert_that(braille.char_to_dots("⠈")).is_equal_to(0x08)  # Dot 4
    assert_that(braille.char_to_dots("⠃")).is_equal_to(0x03)  # Dots 1+2


def test_dots_to_char_roundtrip() -> None:
    """Converting dots to char and back should preserve value."""
    for dots in [0, 1, 127, 255]:
        char = braille.dots_to_char(dots)
        assert_that(braille.char_to_dots(char)).is_equal_to(dots)


def test_char_to_pixels_empty() -> None:
    """Empty braille should produce all-zero pixels."""
    pixels = braille.char_to_pixels("⠀")
    assert_that(pixels.shape).is_equal_to((4, 2))
    assert_that(int(pixels.sum())).is_equal_to(0)


def test_char_to_pixels_full() -> None:
    """Full braille should produce all-one pixels."""
    pixels = braille.char_to_pixels("⣿")
    assert_that(pixels.shape).is_equal_to((4, 2))
    assert_that(int(pixels.sum())).is_equal_to(8)


def test_char_to_pixels_dot1() -> None:
    """Dot 1 should map to pixel position (0, 0)."""
    pixels = braille.char_to_pixels("⠁")
    assert_that(int(pixels[0, 0])).is_equal_to(1)
    assert_that(int(pixels.sum())).is_equal_to(1)


def test_char_to_pixels_dot4() -> None:
    """Dot 4 should map to pixel position (0, 1)."""
    pixels = braille.char_to_pixels("⠈")
    assert_that(int(pixels[0, 1])).is_equal_to(1)
    assert_that(int(pixels.sum())).is_equal_to(1)


def test_char_to_pixels_dot8() -> None:
    """Dot 8 should map to pixel position (3, 1)."""
    pixels = braille.char_to_pixels("⢀")
    assert_that(int(pixels[3, 1])).is_equal_to(1)
    assert_that(int(pixels.sum())).is_equal_to(1)


def test_pixels_to_char_empty() -> None:
    """All-zero pixels should produce empty braille."""
    pixels = np.zeros((4, 2), dtype=np.uint8)
    char = braille.pixels_to_char(pixels, threshold=1)
    assert_that(char).is_equal_to("⠀")


def test_pixels_to_char_full() -> None:
    """All-one pixels should produce full braille."""
    pixels = np.ones((4, 2), dtype=np.uint8)
    char = braille.pixels_to_char(pixels, threshold=1)
    assert_that(char).is_equal_to("⣿")


def test_encode_decode_roundtrip() -> None:
    """Encoding then decoding should preserve the image."""
    original = np.array(
        [
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 1, 0, 0],
            [0, 0, 1, 1],
        ],
        dtype=np.uint8,
    )

    lines = braille.encode_art(original, threshold=1)

    assert_that(lines).is_length(1)
    assert_that(lines[0]).is_length(2)

    decoded = braille.decode_art(lines)
    np.testing.assert_array_equal(decoded, original)


def test_decode_art_handles_varying_widths() -> None:
    """Decode should handle lines of different lengths."""
    lines = ["⣿⣿⣿", "⣿⣿"]  # 3 chars, 2 chars

    pixels = braille.decode_art(lines)

    # Padded to width of longest line: 2 rows * 4 height, 3 cols * 2 width
    assert_that(pixels.shape).is_equal_to((8, 6))


def test_encode_art_pads_to_char_boundary() -> None:
    """Encode should pad images that don't fit char boundaries."""
    original = np.ones((3, 3), dtype=np.uint8)

    lines = braille.encode_art(original, threshold=1)

    # ceil(3/4) = 1 line, ceil(3/2) = 2 chars
    assert_that(lines).is_length(1)
    assert_that(lines[0]).is_length(2)
