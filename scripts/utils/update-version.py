"""Update project version across sources.

This script updates the version in:
- `pyproject.toml` under [project].version
- `lintro/__init__.py` as __version__

Usage:
    uv run python scripts/utils/update-version.py 0.1.1

Notes:
- Validates a basic semver-like version string (allows pre/dev/build tags).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import toml

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9._-]+)?$")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _update_pyproject_version(pyproject_path: Path, version: str) -> str:
    data = toml.loads(_read_text(pyproject_path))
    old = data.get("project", {}).get("version", "")
    data.setdefault("project", {})["version"] = version
    _write_text(pyproject_path, toml.dumps(data))
    return old


def _update_dunder_version(init_path: Path, version: str) -> str:
    content = _read_text(init_path)
    m = re.search(r"^__version__\s*=\s*\"([^\"]+)\"\s*$", content, re.M)
    old = m.group(1) if m else ""
    if m:
        new_content = re.sub(
            r"^__version__\s*=\s*\"([^\"]+)\"\s*$",
            f'__version__ = "{version}"',
            content,
            count=1,
            flags=re.M,
        )
    else:
        # Append if not found
        new_content = content.rstrip() + f'\n__version__ = "{version}"\n'
    _write_text(init_path, new_content)
    return old


def main() -> int:
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
        f"  lintro/__init__.py: {old_dunder or '(none)'} -> {version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
