"""Tool version requirements for lintro.

This module is the single source of truth for external tool version requirements.

External tools are those that users must install separately (not bundled with lintro).
Bundled Python tools (ruff, black, bandit, etc.) are managed via pyproject.toml
dependencies and don't need tracking here.

Version sources:
- npm tools (prettier, oxlint, etc.): Read from package.json
  (Renovate updates it natively)
- Non-npm tools (hadolint, shellcheck, etc.): Defined in TOOL_VERSIONS below
  (Renovate updates via custom regex managers)

For shell scripts that need these versions, use:
    python3 -c "from lintro._tool_versions import get_tool_version; \
print(get_tool_version('toolname'))"
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from lintro.enums.tool_name import ToolName

if TYPE_CHECKING:
    pass

# Non-npm external tools - updated by Renovate via custom regex managers
# Keys use ToolName enum values for type safety
TOOL_VERSIONS: dict[ToolName | str, str] = {
    ToolName.ACTIONLINT: "1.7.5",
    ToolName.CARGO_AUDIT: "0.17.0",
    ToolName.CLIPPY: "1.92.0",
    ToolName.GITLEAKS: "8.21.2",
    ToolName.HADOLINT: "2.12.0",
    ToolName.PYTEST: "8.0.0",
    ToolName.RUSTFMT: "1.8.0",
    ToolName.SEMGREP: "1.50.0",
    ToolName.SHELLCHECK: "0.11.0",
    ToolName.SHFMT: "3.10.0",
    ToolName.SQLFLUFF: "3.0.0",
    ToolName.TAPLO: "0.10.0",
}

# Mapping from npm package names to ToolName for npm-managed tools
# These versions are read from package.json at runtime
_NPM_PACKAGE_TO_TOOL: dict[str, ToolName] = {
    "typescript": ToolName.TSC,
    "prettier": ToolName.PRETTIER,
    "markdownlint-cli2": ToolName.MARKDOWNLINT,
    "oxlint": ToolName.OXLINT,
    "oxfmt": ToolName.OXFMT,
}

# Reverse mapping for lookups
_TOOL_TO_NPM_PACKAGE: dict[ToolName, str] = {
    v: k for k, v in _NPM_PACKAGE_TO_TOOL.items()
}


@lru_cache(maxsize=1)
def _load_npm_versions() -> dict[ToolName, str]:
    """Load npm tool versions from package.json.

    This is cached to avoid repeated file reads.

    Returns:
        Dictionary mapping ToolName to version string for npm-managed tools.
    """
    # Find package.json relative to this file
    package_json_path = Path(__file__).parent.parent / "package.json"

    if not package_json_path.exists():
        return {}

    try:
        data = json.loads(package_json_path.read_text())
        dev_deps = data.get("devDependencies", {})
        deps = data.get("dependencies", {})
        all_deps = {**deps, **dev_deps}

        versions: dict[ToolName, str] = {}
        for npm_pkg, tool_name in _NPM_PACKAGE_TO_TOOL.items():
            if npm_pkg in all_deps:
                # Strip ^ or ~ prefix from version
                versions[tool_name] = all_deps[npm_pkg].lstrip("^~")

        return versions
    except (json.JSONDecodeError, OSError):
        return {}


def get_tool_version(tool_name: ToolName | str) -> str | None:
    """Get the expected version for an external tool.

    Args:
        tool_name: Name of the tool (ToolName enum or string).
            Also accepts npm package names like "typescript" for "tsc".

    Returns:
        Version string if found, None otherwise.
    """
    # Convert string to ToolName if it's an npm package alias
    if isinstance(tool_name, str):
        if tool_name in _NPM_PACKAGE_TO_TOOL:
            tool_name = _NPM_PACKAGE_TO_TOOL[tool_name]
        else:
            # Try to convert string to ToolName enum
            try:
                tool_name = ToolName(tool_name)
            except ValueError:
                return None

    # Check npm-managed tools first
    npm_versions = _load_npm_versions()
    if tool_name in npm_versions:
        return npm_versions[tool_name]

    # Check non-npm tools
    return TOOL_VERSIONS.get(tool_name)


def get_min_version(tool_name: ToolName) -> str:
    """Get the minimum required version for an external tool.

    Use this in tool definitions for the min_version field. Unlike get_tool_version,
    this raises an error if the tool isn't registered, ensuring all external tools
    are tracked.

    Args:
        tool_name: ToolName enum member.

    Returns:
        Version string.

    Raises:
        KeyError: If tool_name is not found in either TOOL_VERSIONS or package.json.
    """
    version = get_tool_version(tool_name)
    if version is None:
        raise KeyError(
            f"Tool '{tool_name}' not found. "
            f"Add it to TOOL_VERSIONS in lintro/_tool_versions.py "
            f"or package.json (for npm tools).",
        )
    return version


def get_all_expected_versions() -> dict[ToolName | str, str]:
    """Get all expected external tool versions.

    Returns:
        Dictionary mapping tool names to version strings.
        Includes both npm-managed and non-npm tools.
    """
    # Start with non-npm tools
    all_versions: dict[ToolName | str, str] = dict(TOOL_VERSIONS)

    # Add npm-managed tools
    npm_versions = _load_npm_versions()
    for tool_name, version in npm_versions.items():
        all_versions[tool_name] = version

    return all_versions


def is_npm_managed(tool_name: ToolName) -> bool:
    """Check if a tool's version is managed via npm/package.json.

    Args:
        tool_name: ToolName enum member.

    Returns:
        True if the tool version comes from package.json, False otherwise.
    """
    return tool_name in _TOOL_TO_NPM_PACKAGE
