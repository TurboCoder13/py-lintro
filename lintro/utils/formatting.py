"""Formatting utilities for core output.

Includes helpers to read multi-section ASCII art files and normalize
ASCII blocks to a fixed size (width/height) while preserving shape.
"""

import secrets
from pathlib import Path


def read_ascii_art(filename: str) -> list[str]:
    """Read ASCII art from a file.

    Args:
        filename: Name of the ASCII art file.

    Returns:
        List of lines from one randomly selected ASCII art section.
    """
    try:
        # Get the path to the ASCII art file
        ascii_art_dir: Path = Path(__file__).parent.parent / "ascii-art"
        file_path: Path = ascii_art_dir / filename

        # Read the file and parse sections
        with file_path.open("r", encoding="utf-8") as f:
            lines: list[str] = [line.rstrip() for line in f.readlines()]

            # Find non-empty sections (separated by empty lines)
            sections: list[list[str]] = []
            current_section: list[str] = []

            for line in lines:
                if line.strip():
                    current_section.append(line)
                elif current_section:
                    sections.append(current_section)
                    current_section = []

            # Add the last section if it's not empty
            if current_section:
                sections.append(current_section)

            # Return a random section if there are multiple, otherwise return all lines
            if sections:
                # Use ``secrets.choice`` to avoid Bandit B311; cryptographic
                # strength is not required here, but this silences the warning.
                return secrets.choice(sections)
            return lines
    except (FileNotFoundError, OSError):
        # Return empty list if file not found or can't be read
        return []


def normalize_ascii_block(
    lines: list[str],
    *,
    width: int,
    height: int,
    align: str = "center",
    valign: str = "middle",
) -> list[str]:
    """Normalize an ASCII block to a fixed width/height.

    Lines are trimmed on the right only (rstrip), then padded to ``width``.
    If a line exceeds ``width``, it is truncated. The whole block is then
    vertically padded/truncated to ``height``.

    Args:
        lines: Original ASCII block lines.
        width: Target width in characters.
        height: Target height in lines.
        align: Horizontal alignment: 'left', 'center', or 'right'.
        valign: Vertical alignment: 'top', 'middle', or 'bottom'.

    Returns:
        list[str]: Normalized lines of length == ``height`` where each line
        has exactly ``width`` characters.
    """
    if width <= 0 or height <= 0:
        return []

    def _pad_line(s: str) -> str:
        s = s.rstrip("\n").rstrip()
        # Truncate if necessary
        if len(s) > width:
            return s[:width]
        space = width - len(s)
        if align == "left":
            return s + (" " * space)
        if align == "right":
            return (" " * space) + s
        # center
        left = space // 2
        right = space - left
        return (" " * left) + s + (" " * right)

    padded_lines: list[str] = [_pad_line(line) for line in lines]

    # Vertical pad/truncate
    if len(padded_lines) >= height:
        # Truncate based on valign
        if valign == "top":
            return padded_lines[:height]
        if valign == "bottom":
            return padded_lines[-height:]
        # middle
        extra = len(padded_lines) - height
        top_cut = extra // 2
        return padded_lines[top_cut : top_cut + height]

    # Need to add blank lines
    blank = " " * width
    missing = height - len(padded_lines)
    if valign == "top":
        return padded_lines + [blank] * missing
    if valign == "bottom":
        return [blank] * missing + padded_lines
    top_pad = missing // 2
    bottom_pad = missing - top_pad
    return [blank] * top_pad + padded_lines + [blank] * bottom_pad


def normalize_ascii_file_sections(
    file_path: Path,
    *,
    width: int,
    height: int,
    align: str = "center",
    valign: str = "middle",
) -> list[list[str]]:
    """Read a multi-section ASCII file and normalize all sections.

    Sections are separated by empty lines. Each section is normalized
    independently and returned as a list of lines.

    Args:
        file_path: Path to the ASCII art file.
        width: Target width.
        height: Target height.
        align: Horizontal alignment.
        valign: Vertical alignment.

    Returns:
        list[list[str]]: List of normalized sections.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            raw_lines: list[str] = [line.rstrip("\n") for line in f]
    except (FileNotFoundError, OSError):
        return []

    sections: list[list[str]] = []
    current: list[str] = []
    for line in raw_lines:
        if line.strip() == "":
            if current:
                sections.append(current)
                current = []
        else:
            current.append(line)
    if current:
        sections.append(current)

    normalized: list[list[str]] = [
        normalize_ascii_block(
            sec,
            width=width,
            height=height,
            align=align,
            valign=valign,
        )
        for sec in sections
    ]
    return normalized
