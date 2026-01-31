"""Tool version requirements for lintro.

This module is the single source of truth for external tool version requirements.
Renovate is configured to update versions directly in this file.

External tools are those that users must install separately (not bundled with lintro).
Bundled Python tools (ruff, black, bandit, etc.) are managed via pyproject.toml
dependencies and don't need tracking here.

To update a version:
1. Edit TOOL_VERSIONS below
2. Renovate will automatically create PRs for updates

For shell scripts that need these versions, use:
    python3 -c "from lintro._tool_versions import TOOL_VERSIONS; \
print(TOOL_VERSIONS['toolname'])"
"""

from __future__ import annotations

from lintro.enums.tool_name import ToolName

# External tools that users must install separately
# These are updated by Renovate via regex matching
# Keys use ToolName enum values (lowercase strings) for type safety
TOOL_VERSIONS: dict[ToolName | str, str] = {
    ToolName.ACTIONLINT: "1.7.5",
    ToolName.CARGO_AUDIT: "0.17.0",
    ToolName.CLIPPY: "1.92.0",
    ToolName.GITLEAKS: "8.21.2",
    ToolName.HADOLINT: "2.12.0",
    ToolName.MARKDOWNLINT: "0.17.2",
    ToolName.OXFMT: "0.27.0",
    ToolName.OXLINT: "1.42.0",
    ToolName.PRETTIER: "3.8.1",
    ToolName.PYTEST: "8.0.0",
    ToolName.RUSTFMT: "1.8.0",
    ToolName.SEMGREP: "1.50.0",
    ToolName.SHELLCHECK: "0.11.0",
    ToolName.SHFMT: "3.10.0",
    ToolName.SQLFLUFF: "3.0.0",
    ToolName.TAPLO: "0.10.0",
    ToolName.TSC: "5.7.3",
}

# Aliases for shell script compatibility (maps package names to tool names)
# Some npm packages have different names than the lintro tool name
_PACKAGE_ALIASES: dict[str, ToolName] = {
    "typescript": ToolName.TSC,  # npm package "typescript" -> tool "tsc"
}


def get_tool_version(tool_name: ToolName | str) -> str | None:
    """Get the expected version for an external tool.

    Args:
        tool_name: Name of the tool (ToolName enum or string).
            Also accepts package aliases like "typescript" for "tsc".

    Returns:
        Version string if found, None otherwise.
    """
    # Check direct lookup first
    if tool_name in TOOL_VERSIONS:
        return TOOL_VERSIONS[tool_name]
    # Check package aliases (e.g., "typescript" -> ToolName.TSC)
    if isinstance(tool_name, str) and tool_name in _PACKAGE_ALIASES:
        return TOOL_VERSIONS.get(_PACKAGE_ALIASES[tool_name])
    return None


def get_min_version(tool_name: ToolName) -> str:
    """Get the minimum required version for an external tool.

    Use this in tool definitions for the min_version field. Unlike get_tool_version,
    this raises an error if the tool isn't registered, ensuring all external tools
    are tracked in TOOL_VERSIONS.

    Args:
        tool_name: ToolName enum member (must exist in TOOL_VERSIONS).

    Returns:
        Version string.

    Raises:
        KeyError: If tool_name is not in TOOL_VERSIONS.
    """
    if tool_name not in TOOL_VERSIONS:
        raise KeyError(
            f"Tool '{tool_name}' not found in TOOL_VERSIONS. "
            f"Add it to lintro/_tool_versions.py to track its minimum version.",
        )
    return TOOL_VERSIONS[tool_name]


def get_all_expected_versions() -> dict[ToolName | str, str]:
    """Get all expected external tool versions.

    Returns:
        Dictionary mapping tool names to version strings.
    """
    return dict(TOOL_VERSIONS)
