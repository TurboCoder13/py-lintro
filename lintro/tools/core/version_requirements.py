"""Tool version requirements checking utilities."""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled

from lintro.enums.tool_name import ToolName
from lintro.tools.core.version_checking import (
    get_install_hints,
    get_minimum_versions,
)
from lintro.tools.core.version_parsing import (
    ToolVersionInfo,
    compare_versions,
    extract_version_from_output,
    parse_version,
)
from lintro.tools.core.version_parsing import (
    check_tool_version as original_check_tool_version,
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


def check_tool_version(tool_name: str, command: list[str]) -> ToolVersionInfo:
    """Delegate to the original version checking function.

    Args:
        tool_name: Name of the tool to check.
        command: Command list to run the tool.

    Returns:
        ToolVersionInfo: Version check results.
    """
    return original_check_tool_version(tool_name, command)


def get_all_tool_versions() -> dict[str, ToolVersionInfo]:
    """Get version information for all supported tools.

    Returns:
        dict[str, ToolVersionInfo]: Dictionary mapping tool names to version info.
    """
    tools = [tool.value for tool in ToolName]

    minimum_versions = get_minimum_versions()
    install_hints = get_install_hints()

    versions = {}
    for tool in tools:
        min_version = minimum_versions.get(tool, "unknown")
        install_hint = install_hints.get(
            tool,
            f"Install {tool} and ensure it's in PATH",
        )
        has_requirements = tool in minimum_versions

        # Create base info - if no requirements, assume check passes
        version_info = ToolVersionInfo(
            name=tool,
            min_version=min_version,
            install_hint=install_hint,
            version_check_passed=not has_requirements,
        )

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
                # Extract version from output
                output = result.stdout + result.stderr
                version_info.current_version = extract_version_from_output(output, tool)

                if version_info.current_version and has_requirements:
                    # Check if version meets requirements
                    version_info.version_check_passed = (
                        compare_versions(
                            version_info.current_version,
                            min_version,
                        )
                        >= 0
                    )
                elif not version_info.current_version:
                    version_info.error_message = (
                        f"Could not parse version from output: {output.strip()}"
                    )
                    version_info.version_check_passed = False
            else:
                version_info.error_message = (
                    f"Command failed with return code {result.returncode}"
                )
                version_info.version_check_passed = False
        except (subprocess.TimeoutExpired, OSError) as e:
            version_info.error_message = str(e)
            version_info.version_check_passed = False

        versions[tool] = version_info

    return versions
