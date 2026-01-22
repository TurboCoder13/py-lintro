"""Tool version requirements and checking utilities.

This module centralizes version management for external lintro tools. Version
requirements are defined in lintro/_tool_versions.py, which is the single source
of truth for tools that users must install separately.

## Single Source of Truth

External tool versions are defined directly in lintro/_tool_versions.py. This ensures:

1. One place to update versions (_tool_versions.py)
2. Renovate can track and update versions automatically via regex matching
3. Installed packages have access to version requirements (no build-time generation)
4. Shell scripts can read versions via:
   python3 -c "from lintro._tool_versions import ..."

Bundled Python tools (ruff, black, bandit, mypy, yamllint, darglint) are managed
via pyproject.toml dependencies and don't need tracking in _tool_versions.py.

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

2. Renovate will automatically track and update the version in pyproject.toml.

3. Add version extraction logic in _extract_version_from_output() if needed.

### For External Tools (user must install separately):
1. Add the version to TOOL_VERSIONS in lintro/_tool_versions.py:
   ```python
   TOOL_VERSIONS = {
       # ... existing tools ...
       "newtool": "1.0.0",
   }
   ```

2. Add a Renovate regex pattern in renovate.json to track updates.

3. Add version extraction logic in _extract_version_from_output() if needed.

### Implementation Steps:
1. Create tool plugin class in lintro/tools/definitions/
2. Use @register_tool decorator from lintro.plugins.registry
3. Inherit from BaseToolPlugin in lintro.plugins.base
4. Set version_command in the ToolDefinition (e.g., ["newtool", "--version"])
5. Test with `lintro versions` command
"""

import os

from loguru import logger

from lintro._tool_versions import TOOL_VERSIONS


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


def get_minimum_versions() -> dict[str, str]:
    """Get minimum version requirements for external tools.

    Returns versions from the _tool_versions module for tools that users
    must install separately.

    Returns:
        dict[str, str]: Dictionary mapping tool names to minimum version strings.
    """
    return TOOL_VERSIONS.copy()


def get_install_hints() -> dict[str, str]:
    """Generate installation hints for external tools.

    Returns:
        dict[str, str]: Dictionary mapping tool names to installation hint strings.
    """
    # Static templates mapping tool -> install hint template with {version} placeholder
    templates: dict[str, str] = {
        "pytest": "Install via: pip install pytest>={version} or uv add pytest>={version}",
        "prettier": "Install via: bun add -d prettier@>={version}",
        "biome": "Install via: bun add -d @biomejs/biome@>={version}",
        "markdownlint": "Install via: bun add -d markdownlint-cli2@>={version}",
        "hadolint": (
            "Install via: https://github.com/hadolint/hadolint/releases (v{version}+)"
        ),
        "actionlint": (
            "Install via: https://github.com/rhysd/actionlint/releases (v{version}+)"
        ),
        "clippy": "Install via: rustup component add clippy (requires Rust {version}+)",
        "rustfmt": "Install via: rustup component add rustfmt (v{version}+)",
        "cargo_audit": "Install via: cargo install cargo-audit (v{version}+)",
        "semgrep": "Install via: pip install semgrep>={version} or brew install semgrep",
        "gitleaks": (
            "Install via: https://github.com/gitleaks/gitleaks/releases (v{version}+)"
        ),
        "shellcheck": (
            "Install via: https://github.com/koalaman/shellcheck/releases (v{version}+)"
        ),
        "shfmt": "Install via: https://github.com/mvdan/sh/releases (v{version}+)",
        "sqlfluff": (
            "Install via: pip install sqlfluff>={version} or uv add sqlfluff>={version}"
        ),
        "taplo": (
            "Install via: cargo install taplo-cli "
            "or download from https://github.com/tamasfe/taplo/releases (v{version}+)"
        ),
    }

    versions = get_minimum_versions()
    hints: dict[str, str] = {}

    # Build hints only for tools that exist in versions
    for tool, template in templates.items():
        version = versions.get(tool)
        if version is not None:
            hints[tool] = template.format(version=version)

    # Warn about tools in versions that don't have templates
    missing = set(versions) - set(templates)
    if missing:
        logger.warning(
            "Missing install hints for tools: %s",
            ", ".join(sorted(missing)),
        )

    return hints
