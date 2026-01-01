"""Version parsing utilities for tool version checking and validation."""

import re
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from functools import lru_cache

from loguru import logger

from lintro.enums.tool_name import ToolName, normalize_tool_name

# Import actual implementations from version_checking with aliases
# to avoid name conflicts
from lintro.tools.core.version_checking import (
    VERSION_CHECK_TIMEOUT,
)
from lintro.tools.core.version_checking import (
    get_install_hints as _get_install_hints_impl,
)
from lintro.tools.core.version_checking import (
    get_minimum_versions as _get_minimum_versions_impl,
)

# Common regex pattern for tools that output simple version numbers
# Matches version strings like "1.2.3", "0.14.0", "25.1", etc.
VERSION_NUMBER_PATTERN: str = r"(\d+(?:\.\d+)*)"

# Tools that use the simple version number pattern
TOOLS_WITH_SIMPLE_VERSION_PATTERN: set[ToolName] = {
    ToolName.BANDIT,
    ToolName.HADOLINT,
    ToolName.PRETTIER,
    ToolName.BIOME,
    ToolName.ACTIONLINT,
    ToolName.DARGLINT,
}


@lru_cache(maxsize=1)
def _get_minimum_versions_cached() -> dict[str, str]:
    """Get minimum version requirements (cached).

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    # Call the imported implementation directly to avoid recursion
    return _get_minimum_versions_impl()


@lru_cache(maxsize=1)
def _get_install_hints_cached() -> dict[str, str]:
    """Get installation hints (cached).

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    # Call the imported implementation directly to avoid recursion
    return _get_install_hints_impl()


def get_minimum_versions() -> dict[str, str]:
    """Get minimum version requirements for all tools.

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    # Return a copy to avoid sharing mutable state
    return dict(_get_minimum_versions_cached())


def get_install_hints() -> dict[str, str]:
    """Get installation hints for tools that don't meet requirements.

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    # Return a copy to avoid sharing mutable state
    return dict(_get_install_hints_cached())


@dataclass
class ToolVersionInfo:
    """Information about a tool's version requirements."""

    name: str = field(default="")
    min_version: str = field(default="")
    install_hint: str = field(default="")
    current_version: str | None = field(default=None)
    version_check_passed: bool = field(default=False)
    error_message: str | None = field(default=None)


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple.

    Args:
        version_str: Version string like "1.2.3" or "0.14.0"

    Returns:
        tuple[int, ...]: Comparable version tuple like (1, 2, 3)

    Raises:
        ValueError: If the version string cannot be parsed.
    """
    # Extract version numbers, handling pre-release suffixes
    # Also handle optional leading 'v' (e.g., "v1.2.3")
    match = re.match(r"^v?(\d+(?:\.\d+)*)", version_str.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Unable to parse version string: {version_str!r}")

    version_part = match.group(1)
    return tuple(int(part) for part in version_part.split("."))


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)

    # Pad shorter version to same length
    max_len = max(len(v1_parts), len(v2_parts))
    v1_padded = v1_parts + (0,) * (max_len - len(v1_parts))
    v2_padded = v2_parts + (0,) * (max_len - len(v2_parts))

    if v1_padded < v2_padded:
        return -1
    elif v1_padded > v2_padded:
        return 1
    else:
        return 0


def check_tool_version(tool_name: str, command: list[str]) -> ToolVersionInfo:
    """Check if a tool meets minimum version requirements.

    Args:
        tool_name: Name of the tool to check
        command: Command list to run the tool (e.g., ["python", "-m", "ruff"])

    Returns:
        ToolVersionInfo: Version check results
    """
    minimum_versions = get_minimum_versions()
    install_hints = get_install_hints()

    min_version = minimum_versions.get(tool_name, "unknown")
    install_hint = install_hints.get(
        tool_name,
        f"Install {tool_name} and ensure it's in PATH",
    )
    has_requirements = tool_name in minimum_versions

    info = ToolVersionInfo(
        name=tool_name,
        min_version=min_version,
        install_hint=install_hint,
        # If no requirements, assume check passes
        version_check_passed=not has_requirements,
    )

    try:
        # Run the tool with --version flag
        version_cmd = command + ["--version"]
        result = subprocess.run(  # nosec B603 - args list, shell=False
            version_cmd,
            capture_output=True,
            text=True,
            timeout=VERSION_CHECK_TIMEOUT,  # Configurable version check timeout
        )

        if result.returncode != 0:
            info.error_message = f"Command failed: {' '.join(version_cmd)}"
            logger.debug(
                f"[VersionCheck] Failed to get version for {tool_name}: "
                f"{info.error_message}",
            )
            return info

        # Extract version from output
        output = result.stdout + result.stderr
        info.current_version = extract_version_from_output(output, tool_name)

        if not info.current_version:
            info.error_message = (
                f"Could not parse version from output: {output.strip()}"
            )
            logger.debug(
                f"[VersionCheck] Failed to parse version for {tool_name}: "
                f"{info.error_message}",
            )
            return info

        # Compare versions
        if min_version != "unknown":
            comparison = compare_versions(info.current_version, min_version)
            info.version_check_passed = comparison >= 0
        else:
            # If min_version is unknown, consider check passed since we got a version
            info.version_check_passed = True

        if not info.version_check_passed:
            info.error_message = (
                f"Version {info.current_version} is below minimum requirement "
                f"{min_version}"
            )
            logger.debug(
                f"[VersionCheck] Version check failed for {tool_name}: "
                f"{info.error_message}",
            )

    except (subprocess.TimeoutExpired, OSError) as e:
        info.error_message = f"Failed to run version check: {e}"
        logger.debug(f"[VersionCheck] Exception checking version for {tool_name}: {e}")

    return info


def extract_version_from_output(output: str, tool_name: str | ToolName) -> str | None:
    """Extract version string from tool --version output.

    Args:
        output: Raw output from tool --version
        tool_name: Name of the tool (to handle tool-specific parsing)

    Returns:
        Optional[str]: Extracted version string, or None if not found
    """
    output = output.strip()
    tool_name = normalize_tool_name(tool_name)

    # Tool-specific patterns first (most reliable)
    if tool_name == ToolName.BLACK:
        # black: "black, 25.9.0 (compiled: yes)"
        match = re.search(r"black,\s+(\d+(?:\.\d+)*)", output, re.IGNORECASE)
        if match:
            return match.group(1)

    elif tool_name in TOOLS_WITH_SIMPLE_VERSION_PATTERN:
        # Tools that output simple version numbers: BANDIT, HADOLINT, PRETTIER,
        # BIOME, ACTIONLINT, DARGLINT
        match = re.search(VERSION_NUMBER_PATTERN, output)
        if match:
            return match.group(1)

    elif tool_name == ToolName.MARKDOWNLINT:
        # markdownlint-cli2: "markdownlint-cli2 v0.19.1 (markdownlint v0.39.0)"
        # Extract the cli2 version (first version number after "v")
        match = re.search(
            r"markdownlint-cli2\s+v(\d+(?:\.\d+)*)",
            output,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
        # Fallback: look for any version pattern
        match = re.search(r"v(\d+(?:\.\d+)+)", output)
        if match:
            return match.group(1)

    elif tool_name == ToolName.CLIPPY:
        # For clippy, we check Rust version instead (clippy is tied to Rust)
        # rustc --version outputs: "rustc 1.92.0 (ded5c06cf 2025-12-08)"
        # cargo clippy --version outputs: "clippy 0.1.92 (ded5c06cf2 2025-12-08)"
        # Extract Rust version from rustc output
        match = re.search(r"rustc\s+(\d+(?:\.\d+)*)", output, re.IGNORECASE)
        if match:
            return match.group(1)
        # Fallback: try clippy version format
        match = re.search(r"clippy\s+(\d+(?:\.\d+)*)", output, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: look for version-like pattern (more restrictive)
    # Match version numbers that look reasonable: 1.2.3, 0.14, 25.1, etc.
    match = re.search(r"\b(\d+(?:\.\d+){0,3})\b", output)
    if match:
        return match.group(1)

    return None
