"""Path filtering and file discovery utilities.

Functions for filtering paths, walking directories, and excluding files based on
patterns.
"""

import fnmatch
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def should_exclude_path(
    path: str,
    exclude_patterns: list[str],
) -> bool:
    """Check if a path should be excluded based on patterns.

    Args:
        path: str: File path to check for exclusion (can be absolute or relative).
        exclude_patterns: list[str]: List of glob patterns to match against.

    Returns:
        bool: True if the path should be excluded, False otherwise.
    """
    if not exclude_patterns:
        return False

    # Normalize to absolute path for consistent comparison
    # This ensures both single files and directory-walked files use the same path format
    try:
        abs_path = os.path.abspath(path)
    except (ValueError, OSError):
        # If path normalization fails, use original path
        abs_path = path

    # Normalize path separators for cross-platform compatibility
    normalized_path: str = abs_path.replace("\\", "/")

    for pattern in exclude_patterns:
        pattern_stripped = pattern.strip()
        if not pattern_stripped:
            continue

        # Handle patterns ending with /* to match everything under that directory
        # e.g., "test_samples/*" should match "test_samples/file.md" and
        # "test_samples/subdir/file.md"
        if pattern_stripped.endswith("/*"):
            dir_pattern = pattern_stripped[:-2]  # Remove "/*"
            # Check if the path contains this directory pattern
            # Match both absolute and relative paths
            if f"/{dir_pattern}/" in normalized_path or normalized_path.startswith(
                f"{dir_pattern}/",
            ):
                return True
            # Also check if it matches the directory name as a path part
            path_parts: list[str] = normalized_path.split("/")
            if dir_pattern in path_parts:
                # Check if the directory appears before the current file
                dir_index = path_parts.index(dir_pattern)
                # If directory is found, exclude everything under it
                if dir_index < len(path_parts) - 1:
                    return True

        # Handle directory-only patterns (no wildcards, no trailing slash)
        # e.g., "build", "dist", ".lintro" should match everything under them
        elif "/" not in pattern_stripped and "*" not in pattern_stripped:
            # Check if this directory name appears in the path
            path_parts = normalized_path.split("/")
            if pattern_stripped in path_parts:
                # If it's a directory in the path, exclude everything under it
                dir_index = path_parts.index(pattern_stripped)
                if dir_index < len(path_parts) - 1:
                    return True

        # Standard glob matching for other patterns
        if fnmatch.fnmatch(normalized_path, pattern_stripped):
            return True
        # Also check if the pattern matches any part of the path
        path_parts = normalized_path.split("/")
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern_stripped):
                return True
    return False


def walk_files_with_excludes(
    paths: list[str],
    file_patterns: list[str],
    exclude_patterns: list[str],
    include_venv: bool = False,
) -> list[str]:
    """Return files under ``paths`` matching patterns and not excluded.

    Args:
        paths: list[str]: Files or directories to search.
        file_patterns: list[str]: Glob patterns to include.
        exclude_patterns: list[str]: Glob patterns to exclude.
        include_venv: bool: Include virtual environment directories when True.

    Returns:
        list[str]: Sorted file paths matching include filters and not excluded.
    """
    all_files: list[str] = []

    for path in paths:
        if os.path.isfile(path):
            # Single file - check if the filename matches any file pattern
            filename = os.path.basename(path)
            for pattern in file_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    # Use absolute path for consistent exclusion checking
                    abs_path = os.path.abspath(path)
                    if not should_exclude_path(
                        path=abs_path,
                        exclude_patterns=exclude_patterns,
                    ):
                        all_files.append(abs_path)
                    break
        elif os.path.isdir(path):
            # Directory - walk through it
            for root, dirs, files in os.walk(path):
                # Filter out virtual environment directories unless include_venv is True
                if not include_venv:
                    dirs[:] = [d for d in dirs if not _is_venv_directory(d)]

                # Check each file against the patterns
                for file in files:
                    file_path: str = os.path.join(root, file)
                    # Use absolute path for consistent exclusion checking
                    abs_file_path: str = os.path.abspath(file_path)

                    # Check if file matches any file pattern
                    matches_pattern: bool = False
                    for pattern in file_patterns:
                        if fnmatch.fnmatch(file, pattern):
                            matches_pattern = True
                            break

                    if matches_pattern and not should_exclude_path(
                        path=abs_file_path,
                        exclude_patterns=exclude_patterns,
                    ):
                        all_files.append(abs_file_path)

    return sorted(all_files)


def _is_venv_directory(dirname: str) -> bool:
    """Check if a directory name indicates a virtual environment.

    Args:
        dirname: str: Directory name to check.

    Returns:
        bool: True if the directory appears to be a virtual environment.
    """
    from lintro.utils.tool_utils import VENV_PATTERNS

    return dirname in VENV_PATTERNS
