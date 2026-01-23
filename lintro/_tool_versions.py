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

# External tools that users must install separately
# These are updated by Renovate via regex matching
TOOL_VERSIONS: dict[str, str] = {
    "actionlint": "1.7.5",
    "biome": "2.3.9",
    "cargo_audit": "0.17.0",
    "clippy": "1.92.0",
    "gitleaks": "8.21.2",
    "hadolint": "2.12.0",
    "markdownlint": "0.17.2",
    "oxfmt": "0.1.0",
    "oxlint": "1.0.0",
    "prettier": "3.7.3",
    "pytest": "8.0.0",
    "rustfmt": "1.8.0",
    "semgrep": "1.50.0",
    "shellcheck": "0.11.0",
    "shfmt": "3.10.0",
    "sqlfluff": "3.0.0",
    "taplo": "0.10.0",
    "typescript": "5.7.3",
}


def get_tool_version(tool_name: str) -> str | None:
    """Get the expected version for an external tool.

    Args:
        tool_name: Name of the tool.

    Returns:
        Version string if found, None otherwise.
    """
    return TOOL_VERSIONS.get(tool_name)


def get_all_expected_versions() -> dict[str, str]:
    """Get all expected external tool versions.

    Returns:
        Dictionary mapping tool names to version strings.
    """
    return TOOL_VERSIONS.copy()
