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
        path: str: File path to check for exclusion.
        exclude_patterns: list[str]: List of glob patterns to match against.

    Returns:
        bool: True if the path should be excluded, False otherwise.
    """
    if not exclude_patterns:
        return False

    # Normalize path separators for cross-platform compatibility
    normalized_path: str = path.replace("\\", "/")

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(normalized_path, pattern):
            return True
        # Also check if the pattern matches any part of the path
        path_parts: list[str] = normalized_path.split("/")
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
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
                    all_files.append(path)
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
                    rel_path: str = os.path.relpath(file_path, path)

                    # Check if file matches any file pattern
                    matches_pattern: bool = False
                    for pattern in file_patterns:
                        if fnmatch.fnmatch(file, pattern):
                            matches_pattern = True
                            break

                    if matches_pattern and not should_exclude_path(
                        path=rel_path,
                        exclude_patterns=exclude_patterns,
                    ):
                        all_files.append(file_path)

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
