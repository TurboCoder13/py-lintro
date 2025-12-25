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

import os
import tomllib
from pathlib import Path

from loguru import logger


def _get_version_timeout() -> int:
    """Return the validated version check timeout.

    Returns:
        int: Timeout in seconds; falls back to default when the env var is invalid.
    """
    default_timeout = 30
    env_value = os.getenv("LINTRO_VERSION_TIMEOUT")
    if env_value is None:
        return default_timeout

    try:
        timeout = int(env_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid LINTRO_VERSION_TIMEOUT '%s'; using default %s",
            env_value,
            default_timeout,
        )
        return default_timeout

    if timeout < 1:
        logger.warning(
            "LINTRO_VERSION_TIMEOUT must be >= 1; using default %s",
            default_timeout,
        )
        return default_timeout

    return timeout


VERSION_CHECK_TIMEOUT: int = _get_version_timeout()


def _load_pyproject_config() -> dict[str, object]:
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

    versions: dict[str, str] = {}

    # Python tools bundled with lintro - extract from dependencies
    python_bundled_tools = {"ruff", "black", "bandit", "yamllint", "darglint", "mypy"}
    project_section = config.get("project", {})
    project_dependencies = (
        project_section.get("dependencies", [])
        if isinstance(project_section, dict)
        else []
    )

    for dep in project_dependencies:
        dep = dep.strip()
        for tool in python_bundled_tools:
            if dep.startswith(f"{tool}>=") or dep.startswith(f"{tool}=="):
                versions[tool] = _parse_version_specifier(dep[len(tool) :])
                break

    # Other tools - read from [tool.lintro.versions] section
    tool_section = (
        config.get("tool", {}) if isinstance(config.get("tool", {}), dict) else {}
    )
    lintro_section = (
        tool_section.get("lintro", {}) if isinstance(tool_section, dict) else {}
    )
    lintro_versions = (
        lintro_section.get("versions", {}) if isinstance(lintro_section, dict) else {}
    )
    if isinstance(lintro_versions, dict):
        versions.update({k: str(v) for k, v in lintro_versions.items()})

    # Fill in any missing tools with defaults (for backward compatibility)
    defaults = {
        "pytest": "8.0.0",
        "prettier": "3.7.0",
        "biome": "2.3.8",
        "hadolint": "2.12.0",
        "actionlint": "1.7.0",
        "markdownlint": "0.16.0",
        "clippy": "1.75.0",
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
    hints: dict[str, str] = {}

    # Python bundled tools
    python_bundled = {"ruff", "black", "bandit", "yamllint", "darglint", "mypy"}
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
            "biome": (
                f"Install via: npm install --save-dev "
                f"@biomejs/biome>={versions.get('biome', '2.3.8')}"
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
            "clippy": (
                f"Install via: rustup component add clippy "
                f"(requires Rust {versions.get('clippy', '1.75.0')}+)"
            ),
        },
    )

    return hints


# Cache the loaded versions to avoid re-reading pyproject.toml repeatedly
_MINIMUM_VERSIONS_CACHE: dict[str, str] | None = None
