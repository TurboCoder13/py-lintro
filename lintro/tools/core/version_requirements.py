"""Tool version requirements checking utilities."""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled

from lintro.tools.core.version_checking import (
    _get_install_hints,
    _get_minimum_versions,
    _parse_version_specifier,
)
from lintro.tools.core.version_parsing import (
    ToolVersionInfo,
    _compare_versions,
    _extract_version_from_output,
    _parse_version,
    get_install_hints,
    get_minimum_versions,
)

__all__ = [
    "ToolVersionInfo",
    "_compare_versions",
    "_extract_version_from_output",
    "_get_install_hints",
    "_get_minimum_versions",
    "_parse_version",
    "_parse_version_specifier",
    "check_tool_version",
    "get_all_tool_versions",
    "get_install_hints",
    "get_minimum_versions",
]


def check_tool_version(tool_name: str, command: list[str]) -> ToolVersionInfo:
    """Delegate to the original version checking function.

    Args:
        tool_name: Name of the tool to check.
        command: Command list to run the tool.

    Returns:
        ToolVersionInfo: Version check results.
    """
    from lintro.tools.core.version_parsing import check_tool_version as original_check

    return original_check(tool_name, command)


def get_all_tool_versions() -> dict[str, ToolVersionInfo]:
    """Get version information for all supported tools.

    Returns:
        dict[str, ToolVersionInfo]: Dictionary mapping tool names to version info.
    """
    tools = [
        "ruff",
        "black",
        "bandit",
        "yamllint",
        "darglint",
        "mypy",
        "pytest",
        "prettier",
        "biome",
        "hadolint",
        "actionlint",
        "markdownlint",
        "clippy",
    ]

    versions = {}
    for tool in tools:
        try:
            cmd = [tool, "--version"]
            result = subprocess.run(  # nosec B603 - tool is controlled
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                versions[tool] = ToolVersionInfo(
                    name=tool,
                    current_version=version_str,
                    version_check_passed=True,
                )
            else:
                versions[tool] = ToolVersionInfo(
                    name=tool,
                    current_version=None,
                    version_check_passed=False,
                    error_message=(
                        f"Command failed with return code {result.returncode}"
                    ),
                )
        except (subprocess.TimeoutExpired, OSError) as e:
            versions[tool] = ToolVersionInfo(
                name=tool,
                current_version=None,
                version_check_passed=False,
                error_message=str(e),
            )

    return versions
