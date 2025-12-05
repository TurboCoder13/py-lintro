"""Tool version requirements and checking utilities.

This module centralizes version management for all lintro tools. Version requirements
are read from pyproject.toml to ensure consistency across the entire codebase.

## Adding a New Tool

When adding a new tool to lintro, follow these steps:

### For Bundled Python Tools (installed with lintro):
1. Add the tool as a dependency in pyproject.toml:
   ```toml
   dependencies = [
       # ... existing deps ...
       "newtool>=1.0.0",
   ]
   ```

2. Update get_all_tool_versions() to include the new tool's command:
   ```python
   tool_commands = {
       # ... existing tools ...
       "newtool": ["newtool"],  # Or ["python", "-m", "newtool"] if module-based
   }
   ```

3. Add version extraction logic in _extract_version_from_output() if needed.

### For External Tools (user must install separately):
1. Add minimum version to [tool.lintro.versions] in pyproject.toml:
   ```toml
   [tool.lintro.versions]
   newtool = "1.0.0"
   ```

2. Update get_all_tool_versions() with the tool's command.

3. Add version extraction logic in _extract_version_from_output() if needed.

### Implementation Steps:
1. Create tool implementation class in lintro/tools/implementations/
2. Add version checking in the tool's check() and fix() methods
3. Update ToolEnum in lintro/tools/tool_enum.py
4. Add tool to tool_commands dict in this file
5. Test with `lintro versions` command

The version system automatically reads from pyproject.toml, so Renovate and other
dependency management tools will keep versions up to date.
"""

import re
import subprocess  # nosec B404 - used safely with shell disabled
import tomllib
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


def _load_pyproject_config() -> dict:
    """Load pyproject.toml configuration.

    Returns:
        dict: Configuration dictionary from pyproject.toml, or empty dict if not found.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        logger.warning("pyproject.toml not found, using default version requirements")
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.warning(f"Failed to load pyproject.toml: {e}")
        return {}


def _parse_version_specifier(specifier: str) -> str:
    """Extract minimum version from a PEP 508 version specifier.

    Args:
        specifier: PEP 508 version specifier string.

    Returns:
        str: Minimum version string extracted from specifier.

    Examples:
        ">=0.14.0" -> "0.14.0"
        "==1.8.1" -> "1.8.1"
        ">=25.0.0,<26.0.0" -> "25.0.0"
    """
    # Split on comma and take the first constraint
    constraints = [c.strip() for c in specifier.split(",")]
    for constraint in constraints:
        if constraint.startswith(">=") or constraint.startswith("=="):
            return constraint[2:]
    # If no recognized constraint, return the specifier as-is
    return specifier.strip()


def _get_minimum_versions() -> dict[str, str]:
    """Get minimum version requirements for all tools from pyproject.toml.

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    config = _load_pyproject_config()

    versions = {}

    # Python tools bundled with lintro - extract from dependencies
    python_bundled_tools = {"ruff", "black", "bandit", "yamllint", "darglint"}
    dependencies = config.get("project", {}).get("dependencies", [])

    for dep in dependencies:
        dep = dep.strip()
        for tool in python_bundled_tools:
            if dep.startswith(f"{tool}>=") or dep.startswith(f"{tool}=="):
                versions[tool] = _parse_version_specifier(dep[len(tool) :])
                break

    # Other tools - read from [tool.lintro.versions] section
    lintro_versions = config.get("tool", {}).get("lintro", {}).get("versions", {})
    versions.update(lintro_versions)

    # Fill in any missing tools with defaults (for backward compatibility)
    defaults = {
        "pytest": "8.0.0",
        "prettier": "3.7.0",
        "hadolint": "2.12.0",
        "actionlint": "1.7.0",
        "markdownlint": "0.16.0",
    }

    for tool, default_version in defaults.items():
        if tool not in versions:
            versions[tool] = default_version

    return versions


def _get_install_hints() -> dict[str, str]:
    """Generate installation hints based on tool type and version requirements.

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    versions = _get_minimum_versions()
    hints = {}

    # Python bundled tools
    python_bundled = {"ruff", "black", "bandit", "yamllint", "darglint"}
    for tool in python_bundled:
        version = versions.get(tool, "latest")
        hints[tool] = (
            f"Install via: pip install {tool}>={version} or uv add {tool}>={version}"
        )

    # Other tools
    pytest_version = versions.get("pytest", "8.0.0")
    hints.update(
        {
            "pytest": (
                f"Install via: pip install pytest>={pytest_version} "
                f"or uv add pytest>={pytest_version}"
            ),
            "prettier": (
                f"Install via: npm install --save-dev "
                f"prettier>={versions.get('prettier', '3.7.0')}"
            ),
            "markdownlint": (
                f"Install via: npm install --save-dev "
                f"markdownlint-cli2>={versions.get('markdownlint', '0.16.0')}"
            ),
            "hadolint": (
                f"Install via: https://github.com/hadolint/hadolint/releases "
                f"(v{versions.get('hadolint', '2.12.0')}+)"
            ),
            "actionlint": (
                f"Install via: https://github.com/rhysd/actionlint/releases "
                f"(v{versions.get('actionlint', '1.7.0')}+)"
            ),
        },
    )

    return hints


# Cache the loaded versions to avoid re-reading pyproject.toml repeatedly
_MINIMUM_VERSIONS_CACHE: dict[str, str] | None = None
_INSTALL_HINTS_CACHE: dict[str, str] | None = None


def get_minimum_versions() -> dict[str, str]:
    """Get minimum version requirements for all tools.

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    global _MINIMUM_VERSIONS_CACHE
    if _MINIMUM_VERSIONS_CACHE is None:
        _MINIMUM_VERSIONS_CACHE = _get_minimum_versions()
    return _MINIMUM_VERSIONS_CACHE


def get_install_hints() -> dict[str, str]:
    """Get installation hints for tools that don't meet requirements.

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    global _INSTALL_HINTS_CACHE
    if _INSTALL_HINTS_CACHE is None:
        _INSTALL_HINTS_CACHE = _get_install_hints()
    return _INSTALL_HINTS_CACHE


@dataclass
class ToolVersionInfo:
    """Information about a tool's version requirements."""

    name: str
    min_version: str
    install_hint: str
    current_version: str | None = None
    version_check_passed: bool = False
    error_message: str | None = None


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple.

    Args:
        version_str: Version string like "1.2.3" or "0.14.0"

    Returns:
        tuple[int, ...]: Comparable version tuple like (1, 2, 3)
    """
    # Extract version numbers, handling pre-release suffixes
    match = re.match(r"^(\d+(?:\.\d+)*)", version_str.strip())
    if not match:
        return (0,)

    version_part = match.group(1)
    return tuple(int(part) for part in version_part.split("."))


def _compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1_parts = _parse_version(version1)
    v2_parts = _parse_version(version2)

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
            timeout=10,  # 10 second timeout
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
        info.current_version = _extract_version_from_output(output, tool_name)

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
        comparison = _compare_versions(info.current_version, min_version)
        info.version_check_passed = comparison >= 0

        if not info.version_check_passed:
            info.error_message = (
                f"Version {info.current_version} is below minimum requirement "
                f"{min_version}"
            )
            logger.debug(
                f"[VersionCheck] Version check failed for {tool_name}: "
                f"{info.error_message}",
            )

    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
        info.error_message = f"Failed to run version check: {e}"
        logger.debug(f"[VersionCheck] Exception checking version for {tool_name}: {e}")

    return info


def _extract_version_from_output(output: str, tool_name: str) -> str | None:
    """Extract version string from tool --version output.

    Args:
        output: Raw output from tool --version
        tool_name: Name of the tool (to handle tool-specific parsing)

    Returns:
        Optional[str]: Extracted version string, or None if not found
    """
    output = output.strip()

    # Tool-specific patterns first (most reliable)
    if tool_name == "black":
        # black: "black, 25.9.0 (compiled: yes)"
        match = re.search(r"black,\s+(\d+(?:\.\d+)*)", output, re.IGNORECASE)
        if match:
            return match.group(1)

    elif tool_name == "bandit":
        # bandit: "__main__.py 1.8.6"
        match = re.search(r"(\d+(?:\.\d+)*)", output)
        if match:
            return match.group(1)

    elif tool_name == "hadolint":
        # hadolint: "Haskell Dockerfile Linter 2.14.0"
        match = re.search(r"(\d+(?:\.\d+)*)", output)
        if match:
            return match.group(1)

    elif tool_name == "prettier":
        # prettier: "Prettier x.y.z" or just version
        match = re.search(r"(\d+(?:\.\d+)*)", output)
        if match:
            return match.group(1)

    elif tool_name == "actionlint":
        # actionlint: "actionlint x.y.z" or just version
        match = re.search(r"(\d+(?:\.\d+)*)", output)
        if match:
            return match.group(1)

    elif tool_name == "darglint":
        # darglint outputs just the version number
        match = re.search(r"(\d+(?:\.\d+)*)", output)
        if match:
            return match.group(1)

    elif tool_name == "markdownlint":
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

    # Fallback: look for any version-like pattern
    match = re.search(r"(\d+(?:\.\d+)+)", output)
    if match:
        return match.group(1)

    return None


def get_all_tool_versions() -> dict[str, ToolVersionInfo]:
    """Get version information for all supported tools.

    Returns:
        dict[str, ToolVersionInfo]: Tool name to version info mapping
    """
    # Define tool commands - this avoids circular imports
    tool_commands = {
        # Python bundled tools (available as scripts when installed)
        "ruff": ["ruff"],
        "black": ["black"],
        "bandit": ["bandit"],
        "yamllint": ["yamllint"],
        "darglint": ["darglint"],
        # Python user tools
        "pytest": ["python", "-m", "pytest"],
        # Node.js tools
        "prettier": ["npx", "--yes", "prettier"],
        "markdownlint": ["npx", "--yes", "markdownlint-cli2"],
        # Binary tools
        "hadolint": ["hadolint"],
        "actionlint": ["actionlint"],
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
