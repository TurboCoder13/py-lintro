"""Tool version requirements checking utilities."""

from __future__ import annotations

from loguru import logger

from lintro.tools.core.version_checking import (
    get_install_hints,
    get_minimum_versions,
)
from lintro.tools.core.version_parsing import (
    ToolVersionInfo,
    check_tool_version,
    compare_versions,
    extract_version_from_output,
    parse_version,
)

__all__ = [
    "ToolVersionInfo",
    "check_tool_version",
    "get_all_tool_versions",
    "compare_versions",
    "extract_version_from_output",
    "get_install_hints",
    "get_minimum_versions",
    "parse_version",
]


def get_all_tool_versions() -> dict[str, ToolVersionInfo]:
    """Get version information for all supported tools.

    Returns:
        dict[str, ToolVersionInfo]: Dictionary mapping tool names to version info.
    """
    # Define tool commands - handles module-based invocation correctly
    tool_commands = {
        # Python bundled tools (available as scripts when installed)
        "ruff": ["ruff"],
        "black": ["black"],
        "bandit": ["bandit"],
        "yamllint": ["yamllint"],
        "darglint": ["darglint"],
        # Python user tools - require module-based invocation
        "mypy": ["python", "-m", "mypy"],
        "pytest": ["python", "-m", "pytest"],
        # Node.js tools
        # Note: Users must install these tools explicitly via npm/npx
        "prettier": ["prettier"],
        "biome": ["biome"],
        "markdownlint": ["markdownlint-cli2"],
        # Binary tools
        "hadolint": ["hadolint"],
        "actionlint": ["actionlint"],
        # Rust/Cargo tools
        "clippy": ["cargo", "clippy"],
    }

    results = {}
    minimum_versions = get_minimum_versions()
    install_hints = get_install_hints()

    for tool_name, command in tool_commands.items():
        try:
            results[tool_name] = check_tool_version(tool_name, command)
        except Exception as e:
            logger.debug(f"Failed to check version for {tool_name}: {e}")
            min_version = minimum_versions.get(tool_name, "unknown")
            install_hint = install_hints.get(tool_name, f"Install {tool_name}")
            results[tool_name] = ToolVersionInfo(
                name=tool_name,
                min_version=min_version,
                install_hint=install_hint,
                error_message=f"Failed to check version: {e}",
            )

    return results
