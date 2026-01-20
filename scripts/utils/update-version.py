"""Update project version across sources.

This script updates the version in:
- `pyproject.toml` under [project].version
- `lintro/__init__.py` as __version__

Usage:
    uv run python scripts/utils/update-version.py 0.1.1

Notes:
- Validates a basic semver-like version string (allows pre/dev/build tags).
- Uses tomlkit for pyproject.toml to preserve formatting, comments, and style.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomlkit

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9._-]+)?$")


def _read_text(path: Path) -> str:
    """Read text from a UTF-8 file.

    Args:
        path: File to read.

    Returns:
        File contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    """Write text to a UTF-8 file, replacing existing contents.

    Args:
        path: File to write.
        content: New file contents.
    """
    path.write_text(content, encoding="utf-8")


def _update_pyproject_version(pyproject_path: Path, version: str) -> str:
    """Update ``project.version`` in ``pyproject.toml``.

    Uses tomlkit to preserve existing file formatting, comments, and style.

    Args:
        pyproject_path: Path to the project TOML file.
        version: New version string to set.

    Returns:
        Previous version string if present, otherwise empty string.
    """
    content = _read_text(pyproject_path)
    doc = tomlkit.parse(content)
    old = str(doc.get("project", {}).get("version", ""))
    doc["project"]["version"] = version
    _write_text(pyproject_path, tomlkit.dumps(doc))
    return old


def _update_dunder_version(init_path: Path, version: str) -> str:
    """Update ``__version__`` assignment in ``__init__.py``.

    Uses regex substitution to preserve existing file formatting.

    Args:
        init_path: Path to the package ``__init__.py``.
        version: New version string to write.

    Returns:
        Previous version string if found, otherwise empty string.
    """
    content = _read_text(init_path)
    m = re.search(r'^(__version__\s*=\s*)"[^"]+"', content, re.M)
    old_match = re.search(r'^__version__\s*=\s*"([^"]+)"', content, re.M)
    old = old_match.group(1) if old_match else ""
    if m:
        new_content = re.sub(
            r'^(__version__\s*=\s*)"[^"]+"',
            rf'\g<1>"{version}"',
            content,
            count=1,
            flags=re.M,
        )
    else:
        # Append if not found
        new_content = content.rstrip() + f'\n__version__ = "{version}"\n'
    # Ensure file ends with exactly one newline
    new_content = new_content.rstrip() + "\n"
    _write_text(init_path, new_content)
    return old


def main() -> int:
    """CLI entry to update project version across sources.

    Returns:
        Process exit code (0 on success, 2 on usage/validation failure).
    """
    if len(sys.argv) != 2:
        print("Usage: update-version.py <version>", file=sys.stderr)
        return 2
    version = sys.argv[1].strip()
    if not VERSION_PATTERN.match(version):
        print(f"Invalid version: {version}", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    pyproject = repo_root / "pyproject.toml"
    init_py = repo_root / "lintro" / "__init__.py"

    old_pyproject = _update_pyproject_version(pyproject_path=pyproject, version=version)
    old_dunder = _update_dunder_version(init_path=init_py, version=version)

    print(
        f"Updated version -> {version}\n"
        f"  pyproject.toml: {old_pyproject or '(none)'} -> {version}\n"
        f"  lintro/__init__.py: {old_dunder or '(none)'} -> {version}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
