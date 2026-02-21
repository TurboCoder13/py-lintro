"""Braille character encoding/decoding for ASCII art.

Braille Unicode characters (U+2800-U+28FF) represent a 2x4 dot grid.
Each character encodes 8 pixels, making them ideal for pixel art.

Dot positions and their bit values:
    1 4     (0x01) (0x08)
    2 5     (0x02) (0x10)
    3 6     (0x04) (0x20)
    7 8     (0x40) (0x80)
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Braille Unicode block starts at U+2800
BRAILLE_BASE = 0x2800

# Pixels per Braille character
CHAR_HEIGHT = 4
CHAR_WIDTH = 2

# Dot positions map to bits: dots are numbered 1-8
# Dot layout in 2x4 grid (row, col) -> bit value
DOT_BITS: dict[tuple[int, int], int] = {
    (0, 0): 0x01,  # dot 1
    (1, 0): 0x02,  # dot 2
    (2, 0): 0x04,  # dot 3
    (0, 1): 0x08,  # dot 4
    (1, 1): 0x10,  # dot 5
    (2, 1): 0x20,  # dot 6
    (3, 0): 0x40,  # dot 7
    (3, 1): 0x80,  # dot 8
}


def is_braille(char: str) -> bool:
    """Check if a character is a Braille Unicode character."""
    if len(char) != 1:
        return False
    code = ord(char)
    return BRAILLE_BASE <= code <= BRAILLE_BASE + 0xFF


def char_to_dots(char: str) -> int:
    """Convert a Braille character to its dot pattern (0-255)."""
    if not is_braille(char):
        return 0
    return ord(char) - BRAILLE_BASE


def dots_to_char(dots: int) -> str:
    """Convert a dot pattern (0-255) to a Braille character."""
    return chr(BRAILLE_BASE + (dots & 0xFF))


def char_to_pixels(char: str) -> NDArray[np.uint8]:
    """Decode a single Braille character to a 4x2 pixel array.

    Args:
        char: A single Braille Unicode character.

    Returns:
        4x2 numpy array where 1 = dot present, 0 = no dot.

    """
    pixels = np.zeros((4, 2), dtype=np.uint8)
    dots = char_to_dots(char)

    for (row, col), bit in DOT_BITS.items():
        if dots & bit:
            pixels[row, col] = 1

    return pixels


def pixels_to_char(pixels: NDArray[np.uint8], threshold: int = 128) -> str:
    """Encode a 4x2 pixel array to a Braille character.

    Args:
        pixels: 4x2 array of pixel values (0-255 or 0-1).
        threshold: Values >= threshold become dots. Default 128 for
                   grayscale, use 1 for binary arrays.

    Returns:
        A single Braille Unicode character.

    """
    dots = 0
    for (row, col), bit in DOT_BITS.items():
        if (
            row < pixels.shape[0]
            and col < pixels.shape[1]
            and pixels[row, col] >= threshold
        ):
            dots |= bit

    return dots_to_char(dots)


def decode_art(lines: list[str]) -> NDArray[np.uint8]:
    """Decode Braille art to a pixel bitmap.

    Args:
        lines: List of strings containing Braille art.

    Returns:
        2D numpy array (height, width) of pixel values (0 or 1).

    """
    if not lines:
        return np.zeros((0, 0), dtype=np.uint8)

    max_chars_wide = max(len(line) for line in lines)
    char_rows = len(lines)

    pixel_height = char_rows * CHAR_HEIGHT
    pixel_width = max_chars_wide * CHAR_WIDTH
    pixels = np.zeros((pixel_height, pixel_width), dtype=np.uint8)

    for row_idx, line in enumerate(lines):
        for col_idx, char in enumerate(line):
            if is_braille(char):
                cpixels = char_to_pixels(char)
                y = row_idx * CHAR_HEIGHT
                x = col_idx * CHAR_WIDTH
                pixels[y : y + CHAR_HEIGHT, x : x + CHAR_WIDTH] = cpixels

    return pixels


def encode_art(
    pixels: NDArray[np.uint8],
    threshold: int = 1,
) -> list[str]:
    """Encode a pixel bitmap to Braille art.

    Args:
        pixels: 2D array (height, width) of pixel values.
        threshold: Pixel value threshold for "on" dots.

    Returns:
        List of strings containing Braille art.

    """
    if pixels.size == 0:
        return []

    height, width = pixels.shape

    pad_height = (CHAR_HEIGHT - height % CHAR_HEIGHT) % CHAR_HEIGHT
    pad_width = (CHAR_WIDTH - width % CHAR_WIDTH) % CHAR_WIDTH

    if pad_height or pad_width:
        pixels = np.pad(
            pixels,
            ((0, pad_height), (0, pad_width)),
            mode="constant",
            constant_values=0,
        )

    height, width = pixels.shape
    char_rows = height // CHAR_HEIGHT
    char_cols = width // CHAR_WIDTH

    lines = []
    for row in range(char_rows):
        line_chars = []
        for col in range(char_cols):
            y = row * CHAR_HEIGHT
            x = col * CHAR_WIDTH
            block = pixels[y : y + CHAR_HEIGHT, x : x + CHAR_WIDTH]
            char = pixels_to_char(block, threshold=threshold)
            line_chars.append(char)
        lines.append("".join(line_chars))

    return lines
