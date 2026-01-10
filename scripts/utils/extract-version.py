#!/usr/bin/env python3
"""Extract the project version from a TOML file.

This utility reads a TOML file (default: ``pyproject.toml``) and prints a
single line in the form ``version=X.Y.Z`` to stdout. It is designed for
easy consumption in CI (append to ``$GITHUB_OUTPUT``) and for reuse across
workflows to avoid inline heredoc Python.

Usage:
    python scripts/utils/extract-version.py [--file PATH]

Examples:
    # Print version from repo pyproject
    python scripts/utils/extract-version.py

    # Print version from an alternate file
    python scripts/utils/extract-version.py --file /tmp/prev.toml
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path


def _load_toml_bytes(path: Path) -> bytes:
    """Load raw TOML bytes from a file.

    Args:
        path: Path to the TOML file.

    Returns:
        Raw file contents as bytes.
    """
    return path.read_bytes()


def _read_version_from_toml_bytes(data: bytes) -> str:
    """Parse TOML bytes and extract ``project.version``.

    Args:
        data: The TOML file contents as bytes.

    Returns:
        The project version string.

    Raises:
        SystemExit: If parsing fails or the version key is missing/invalid.
    """
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"Failed to parse TOML: {exc}") from None

    try:
        version = parsed["project"]["version"]
    except KeyError as exc:
        raise SystemExit(f"Missing project.version in TOML: {exc}") from None
    if not isinstance(version, str) or not version:
        raise SystemExit("Invalid project.version value")
    return version


def main(argv: list[str] | None = None) -> int:
    """CLI entry to extract and print the project version.

    Args:
        argv: Optional argument vector for testing.

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(description="Extract version from TOML")
    parser.add_argument(
        "--file",
        dest="file_path",
        default="pyproject.toml",
        help="Path to TOML file (default: pyproject.toml)",
    )
    args = parser.parse_args(argv)

    path = Path(args.file_path)
    if not path.exists():
        print("version=", end="")
        return 0

    version = _read_version_from_toml_bytes(_load_toml_bytes(path))
    print(f"version={version}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
