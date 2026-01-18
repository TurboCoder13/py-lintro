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
1. Create tool plugin class in lintro/tools/definitions/
2. Use @register_tool decorator from lintro.plugins.registry
3. Inherit from BaseToolPlugin in lintro.plugins.base
4. Set version_command in the ToolDefinition (e.g., ["newtool", "--version"])
5. Test with `lintro versions` command

The version system automatically reads from pyproject.toml, so Renovate and other
dependency management tools will keep versions up to date.
"""

import os
import tomllib
from pathlib import Path

from loguru import logger

_PYTHON_BUNDLED_TOOLS = {"ruff", "black", "bandit", "yamllint", "darglint", "mypy"}


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
    # Search for pyproject.toml starting from module location and moving upwards
    current_dir = Path(os.path.dirname(__file__))
    pyproject_path = None

    for dir_path in [current_dir] + list(current_dir.parents):
        candidate = dir_path / "pyproject.toml"
        if candidate.exists():
            pyproject_path = candidate
            break

    if pyproject_path is None:
        logger.warning("pyproject.toml not found, using default version requirements")
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.warning(f"Failed to load pyproject.toml: {e}")
        return {}


def _parse_version_specifier(specifier: str) -> str:
    """Extract minimum version from a PEP 508 version specifier.

    Handles PEP 508 compliant specifiers including:
    - Extras: package[extra]>=1.0
    - Markers: package>=1.0; python_version>="3.8"
    - Multiple constraints: package>=1.0,<2.0
    - URL dependencies: package @ https://... (returns specifier as-is)

    Args:
        specifier: PEP 508 version specifier string.

    Returns:
        str: Minimum version string extracted from specifier.

    Examples:
        ">=0.14.0" -> "0.14.0"
        "==1.8.1" -> "1.8.1"
        ">=25.0.0,<26.0.0" -> "25.0.0"
        "package[extra]>=1.0" -> "1.0"
        "package>=1.0; python_version>='3.8'" -> "1.0"
    """
    # Handle URL dependencies (format: package @ https://...)
    if " @ " in specifier:
        # For URL dependencies, return the specifier as-is
        # as we can't extract a meaningful version
        return specifier.strip()

    # Split on semicolon to separate markers (PEP 508 format)
    # Format: "package>=1.0; python_version>='3.8'"
    parts = specifier.split(";", 1)
    version_part = parts[0].strip()

    # Handle extras (format: package[extra]>=1.0)
    # Extract the version specifier part after the closing bracket
    if "]" in version_part:
        bracket_end = version_part.rfind("]")
        if bracket_end < len(version_part) - 1:
            version_part = version_part[bracket_end + 1 :].strip()
        else:
            # Malformed: bracket at end, return as-is
            return specifier.strip()

    # Split on comma to handle multiple constraints
    # Format: ">=1.0,<2.0" -> process each constraint
    constraints = [c.strip() for c in version_part.split(",")]
    for constraint in constraints:
        if (
            constraint.startswith(">=")
            or constraint.startswith("==")
            or constraint.startswith("~=")
        ):
            return constraint[2:].strip()
        elif constraint.startswith(">"):
            return constraint[1:].strip()
    # If no recognized constraint, return the cleaned specifier as-is
    return version_part.strip() if version_part else specifier.strip()


def get_minimum_versions() -> dict[str, str]:
    """Get minimum version requirements for all tools from pyproject.toml.

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    config = _load_pyproject_config()

    versions: dict[str, str] = {}

    # Python tools bundled with lintro - extract from dependencies
    python_bundled_tools = _PYTHON_BUNDLED_TOOLS
    project_section = config.get("project", {})
    project_dependencies = (
        project_section.get("dependencies", [])
        if isinstance(project_section, dict)
        else []
    )

    for dep in project_dependencies:
        dep = dep.strip()
        for tool in python_bundled_tools:
            # Handle dependencies with extras: tool[extra]>=version
            # Match both "tool>=" and "tool[extra]>=" patterns
            if dep.startswith(f"{tool}>=") or dep.startswith(f"{tool}=="):
                # Extract version specifier after tool name
                versions[tool] = _parse_version_specifier(dep[len(tool) :])
                break
            elif dep.startswith(f"{tool}[") and (">=" in dep or "==" in dep):
                # Handle extras: find the version specifier after the closing bracket
                bracket_end = dep.find("]", len(tool))
                if bracket_end != -1 and bracket_end < len(dep) - 1:
                    # Extract version specifier after "]"
                    version_spec = dep[bracket_end + 1 :].strip()
                    versions[tool] = _parse_version_specifier(version_spec)
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


def get_install_hints() -> dict[str, str]:
    """Generate installation hints based on tool type and version requirements.

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    versions = get_minimum_versions()
    hints: dict[str, str] = {}

    # Python bundled tools
    for tool in _PYTHON_BUNDLED_TOOLS:
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
                f"Install via: bun add -d "
                f"prettier@>={versions.get('prettier', '3.7.0')}"
            ),
            "biome": (
                f"Install via: bun add -d "
                f"@biomejs/biome@>={versions.get('biome', '2.3.8')}"
            ),
            "markdownlint": (
                f"Install via: bun add -d "
                f"markdownlint-cli2@>={versions.get('markdownlint', '0.16.0')}"
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
            "rustfmt": (
                f"Install via: rustup component add rustfmt "
                f"(v{versions.get('rustfmt', '1.5.0')}+)"
            ),
            "cargo_audit": (
                f"Install via: cargo install cargo-audit "
                f"(v{versions.get('cargo_audit', '0.17.0')}+)"
            ),
            "semgrep": (
                f"Install via: pip install semgrep>="
                f"{versions.get('semgrep', '1.50.0')} or brew install semgrep"
            ),
            "gitleaks": (
                f"Install via: https://github.com/gitleaks/gitleaks/releases "
                f"(v{versions.get('gitleaks', '8.18.0')}+)"
            ),
            "shellcheck": (
                f"Install via: https://github.com/koalaman/shellcheck/releases "
                f"(v{versions.get('shellcheck', '0.9.0')}+)"
            ),
            "shfmt": (
                f"Install via: https://github.com/mvdan/sh/releases "
                f"(v{versions.get('shfmt', '3.7.0')}+)"
            ),
            "sqlfluff": (
                f"Install via: pip install sqlfluff>="
                f"{versions.get('sqlfluff', '3.0.0')} "
                f"or uv add sqlfluff>={versions.get('sqlfluff', '3.0.0')}"
            ),
            "taplo": (
                f"Install via: cargo install taplo-cli "
                f"or download from https://github.com/tamasfe/taplo/releases "
                f"(e.g., {versions.get('taplo', '0.8.0')} or release-taplo-cli-"
                f"{versions.get('taplo', '0.8.0')})"
            ),
        },
    )

    return hints
