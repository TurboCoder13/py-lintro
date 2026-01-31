#!/usr/bin/env python3
"""Verify tool versions are correctly loaded from their sources.

This script validates that:
1. npm tool versions are correctly read from package.json
2. Non-npm tool versions are defined in _tool_versions.py
3. All expected tools have versions available

Exit codes:
    0: All versions are correctly loaded
    1: Missing versions or error occurred
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Verify tool versions are correctly loaded."""
    # Find project root (script is in scripts/ci/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print(f"Checking version loading in: {project_root}")
    print()

    # Add project to path for imports
    sys.path.insert(0, str(project_root))

    from lintro._tool_versions import (
        _NPM_PACKAGE_TO_TOOL,
        TOOL_VERSIONS,
        get_tool_version,
        is_npm_managed,
    )
    from lintro.enums.tool_name import ToolName

    errors: list[str] = []

    # Check that all npm-managed tools have versions from package.json
    print("npm-managed tools (from package.json):")
    for npm_pkg, tool_name in _NPM_PACKAGE_TO_TOOL.items():
        version = get_tool_version(tool_name)
        if version:
            print(f"  ✓ {tool_name.value} ({npm_pkg}): {version}")
        else:
            errors.append(f"npm tool '{tool_name.value}' ({npm_pkg}) has no version")
            print(f"  ✗ {tool_name.value} ({npm_pkg}): MISSING")

    print()

    # Check that all non-npm tools have versions
    print("Non-npm tools (from _tool_versions.py):")
    for tool_name_key, version in TOOL_VERSIONS.items():
        if isinstance(tool_name_key, ToolName):
            print(f"  ✓ {tool_name_key.value}: {version}")

    print()

    # Verify is_npm_managed returns correct values
    print("Verifying npm-managed detection:")
    for tool_name in _NPM_PACKAGE_TO_TOOL.values():
        if not is_npm_managed(tool_name):
            errors.append(f"is_npm_managed({tool_name}) should be True")
            print(f"  ✗ {tool_name.value} should be npm-managed")
        else:
            print(f"  ✓ {tool_name.value} correctly identified as npm-managed")

    for tool_name_key in TOOL_VERSIONS:
        if isinstance(tool_name_key, ToolName) and is_npm_managed(tool_name_key):
            errors.append(f"is_npm_managed({tool_name_key}) should be False")
            print(f"  ✗ {tool_name_key.value} should NOT be npm-managed")

    print()

    if errors:
        print("✗ Errors found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("✓ All tool versions are correctly loaded from their sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
