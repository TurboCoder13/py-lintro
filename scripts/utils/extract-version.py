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
from pathlib import Path


def _load_toml_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _read_version_from_toml_bytes(data: bytes) -> str:
    # Prefer stdlib tomllib (Python 3.11+); fall back to 'toml' if present
    try:
        import tomllib  # type: ignore[attr-defined]

        parsed = tomllib.loads(data.decode("utf-8"))
    except Exception:  # pragma: no cover - fallback path for older envs
        try:
            import toml  # type: ignore

            parsed = toml.loads(data.decode("utf-8"))
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"Failed to parse TOML: {exc}")

    try:
        version = parsed["project"]["version"]
    except Exception as exc:
        raise SystemExit(f"Missing project.version in TOML: {exc}")
    if not isinstance(version, str) or not version:
        raise SystemExit("Invalid project.version value")
    return version


def main(argv: list[str] | None = None) -> int:
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
