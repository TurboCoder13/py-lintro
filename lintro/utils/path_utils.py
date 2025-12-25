"""Path utilities for Lintro.

Small helpers to normalize paths for display consistency.
"""

import os
from pathlib import Path

from loguru import logger


def find_lintro_ignore() -> Path | None:
    """Find .lintro-ignore file by searching upward from current directory.

    Searches upward from the current working directory to find the project root
    by looking for .lintro-ignore or pyproject.toml files.

    Returns:
        Path | None: Path to .lintro-ignore file if found, None otherwise.
    """
    current_dir = Path.cwd()
    # Limit search to prevent infinite loops (e.g., if we're in /)
    max_depth = 20
    depth = 0

    while depth < max_depth:
        lintro_ignore_path = current_dir / ".lintro-ignore"
        if lintro_ignore_path.exists():
            return lintro_ignore_path

        # Also check for pyproject.toml as project root indicator
        pyproject_path = current_dir / "pyproject.toml"
        if pyproject_path.exists():
            # If pyproject.toml exists, check for .lintro-ignore in same directory
            lintro_ignore_path = current_dir / ".lintro-ignore"
            if lintro_ignore_path.exists():
                return lintro_ignore_path
            # Even if .lintro-ignore doesn't exist, we found project root
            # Return None to indicate no .lintro-ignore found
            return None

        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            # Reached filesystem root
            break
        current_dir = parent_dir
        depth += 1

    return None


def load_lintro_ignore() -> list[str]:
    """Load ignore patterns from .lintro-ignore file.

    Returns:
        list[str]: List of ignore patterns.
    """
    ignore_patterns: list[str] = []
    lintro_ignore_path = find_lintro_ignore()

    if lintro_ignore_path and lintro_ignore_path.exists():
        try:
            with open(lintro_ignore_path, encoding="utf-8") as f:
                for line in f:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith("#"):
                        continue
                    ignore_patterns.append(line_stripped)
        except Exception as e:
            logger.warning(f"Failed to load .lintro-ignore: {e}")

    return ignore_patterns


def normalize_file_path_for_display(file_path: str) -> str:
    """Normalize file path to be relative to project root for consistent display.

    This ensures all tools show file paths in the same format:
    - Relative to project root (like ./src/file.py)
    - Consistent across all tools regardless of how they output paths

    Args:
        file_path: File path (can be absolute or relative). If empty, returns as is.

    Returns:
        Normalized relative path from project root (e.g., "./src/file.py")
    """
    # Fast-path: empty or whitespace-only input
    if not file_path or not str(file_path).strip():
        return file_path
    try:
        # Get the current working directory (project root)
        project_root: str = os.getcwd()

        # Convert to absolute path first, then make relative to project root
        abs_path: str = os.path.abspath(file_path)
        rel_path: str = os.path.relpath(abs_path, project_root)

        # Ensure it starts with "./" for consistency (like darglint format)
        if not rel_path.startswith("./") and not rel_path.startswith("../"):
            rel_path = "./" + rel_path

        return rel_path

    except (ValueError, OSError):
        # If path normalization fails, return the original path
        return file_path
