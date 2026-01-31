#!/usr/bin/env python3
"""Verify tool versions are synchronized between package.json and _tool_versions.py.

This script ensures that npm packages managed by Renovate in package.json
have matching versions in lintro/_tool_versions.py.

Exit codes:
    0: All versions are synchronized
    1: Version mismatch detected or error occurred
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Map npm package names to lintro tool names
# These are tools that exist in both package.json and _tool_versions.py
NPM_TOOL_MAPPING: dict[str, str] = {
    "prettier": "prettier",
    "markdownlint-cli2": "markdownlint",
    "oxlint": "oxlint",
    "oxfmt": "oxfmt",
    "typescript": "tsc",
}


def strip_caret(version: str) -> str:
    """Strip caret prefix from npm version string."""
    return version.lstrip("^~")


def load_package_json(project_root: Path) -> dict[str, str]:
    """Load and parse package.json, returning devDependencies versions."""
    package_json_path = project_root / "package.json"
    if not package_json_path.exists():
        print(f"ERROR: package.json not found at {package_json_path}", file=sys.stderr)
        sys.exit(1)

    with package_json_path.open() as f:
        data = json.load(f)

    dev_deps = data.get("devDependencies", {})
    deps = data.get("dependencies", {})

    # Merge, with devDependencies taking precedence
    all_deps = {**deps, **dev_deps}

    return {pkg: strip_caret(ver) for pkg, ver in all_deps.items()}


def load_tool_versions(project_root: Path) -> dict[str, str]:
    """Load tool versions from _tool_versions.py using get_tool_version."""
    import runpy

    sys.path.insert(0, str(project_root))
    tool_versions_path = project_root / "lintro" / "_tool_versions.py"

    if not tool_versions_path.exists():
        print(
            f"ERROR: _tool_versions.py not found at {tool_versions_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    mod = runpy.run_path(str(tool_versions_path))
    get_tool_version = mod["get_tool_version"]

    versions = {}
    for npm_pkg, tool_name in NPM_TOOL_MAPPING.items():
        version = get_tool_version(tool_name)
        if version:
            versions[npm_pkg] = version

    return versions


def main() -> int:
    """Check for version mismatches between package.json and _tool_versions.py."""
    # Find project root (script is in scripts/ci/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print(f"Checking version sync in: {project_root}")
    print()

    package_versions = load_package_json(project_root)
    tool_versions = load_tool_versions(project_root)

    mismatches: list[tuple[str, str, str, str]] = []
    missing_in_tools: list[str] = []
    missing_in_package_json: list[str] = []

    for npm_pkg, tool_name in NPM_TOOL_MAPPING.items():
        pkg_version = package_versions.get(npm_pkg)
        tool_version = tool_versions.get(npm_pkg)

        if pkg_version is None:
            missing_in_package_json.append(npm_pkg)
            continue

        if tool_version is None:
            missing_in_tools.append(npm_pkg)
            continue

        if pkg_version != tool_version:
            mismatches.append((npm_pkg, tool_name, pkg_version, tool_version))

    # Report results
    if not mismatches and not missing_in_tools and not missing_in_package_json:
        print("✓ All tool versions are synchronized")
        print()
        print("Checked packages:")
        for npm_pkg, tool_name in NPM_TOOL_MAPPING.items():
            pkg_version = package_versions.get(npm_pkg)
            if pkg_version:
                print(f"  {npm_pkg} ({tool_name}): {pkg_version}")
        return 0

    print("✗ Version synchronization issues found:")
    print()

    if mismatches:
        print("Version mismatches:")
        print("-" * 60)
        print(f"{'Package':<20} {'package.json':<15} {'_tool_versions.py':<15}")
        print("-" * 60)
        for npm_pkg, _tool_name, pkg_ver, tool_ver in mismatches:
            print(f"{npm_pkg:<20} {pkg_ver:<15} {tool_ver:<15}")
        print()

    if missing_in_tools:
        print("Missing from _tool_versions.py:")
        for pkg in missing_in_tools:
            pkg_version = package_versions.get(pkg, "unknown")
            print(f"  {pkg}: {pkg_version}")
        print()

    if missing_in_package_json:
        print("Missing from package.json (but in NPM_TOOL_MAPPING):")
        for pkg in missing_in_package_json:
            tool_version = tool_versions.get(pkg, "unknown")
            print(f"  {pkg}: {tool_version} (in _tool_versions.py)")
        print()

    print("To fix:")
    print("  1. Update lintro/_tool_versions.py to match package.json versions")
    print("  2. Or update package.json to match _tool_versions.py versions")
    print("  3. If a package was intentionally removed, update NPM_TOOL_MAPPING")
    print()
    print("Renovate should keep these in sync, but manual updates may cause drift.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
