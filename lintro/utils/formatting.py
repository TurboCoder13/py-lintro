"""Formatting utilities for core output."""

from pathlib import Path


def read_ascii_art(filename: str) -> list[str]:
    """Read ASCII art from a file.

    Args:
        filename: Name of the ASCII art file.

    Returns:
        List of lines from one randomly selected ASCII art section.
    """
    import random

    try:
        # Get the path to the ASCII art file
        ascii_art_dir = Path(__file__).parent.parent / "ascii-art"
        file_path = ascii_art_dir / filename

        # Read the file and parse sections
        with file_path.open("r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]

            # Find non-empty sections (separated by empty lines)
            sections = []
            current_section = []

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
                return random.choice(sections)
            return lines
    except (FileNotFoundError, OSError):
        # Return empty list if file not found or can't be read
        return []
