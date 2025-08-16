"""Path utilities for Lintro."""

import os


def normalize_file_path_for_display(file_path: str) -> str:
    """Normalize file path to be relative to project root for consistent display.

    This ensures all tools show file paths in the same format:
    - Relative to project root (like ./src/file.py)
    - Consistent across all tools regardless of how they output paths

    Args:
        file_path: File path (can be absolute or relative)

    Returns:
        Normalized relative path from project root (e.g., "./src/file.py")
    """
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
