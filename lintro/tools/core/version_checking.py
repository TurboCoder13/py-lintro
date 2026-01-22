"""Tool version requirements and checking utilities.

This module centralizes version management for external lintro tools. Version
requirements are defined in lintro/_tool_versions.py, which is the single source
of truth for tools that users must install separately.

## Single Source of Truth

External tool versions are defined directly in lintro/_tool_versions.py. This ensures:

1. One place to update versions (_tool_versions.py)
2. Renovate can track and update versions automatically via regex matching
3. Installed packages have access to version requirements (no build-time generation)
4. Shell scripts can read versions via: python3 -c "from lintro._tool_versions import ..."

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

    Raises:
        KeyError: If a tool is missing from TOOL_VERSIONS (indicates code out of sync).
    """
    versions = get_minimum_versions()
    hints: dict[str, str] = {
        "pytest": (
            f"Install via: pip install pytest>={versions['pytest']} "
            f"or uv add pytest>={versions['pytest']}"
        ),
        "prettier": (
            f"Install via: bun add -d "
            f"prettier@>={versions['prettier']}"
        ),
        "biome": (
            f"Install via: bun add -d "
            f"@biomejs/biome@>={versions['biome']}"
        ),
        "markdownlint": (
            f"Install via: bun add -d "
            f"markdownlint-cli2@>={versions['markdownlint']}"
        ),
        "hadolint": (
            f"Install via: https://github.com/hadolint/hadolint/releases "
            f"(v{versions['hadolint']}+)"
        ),
        "actionlint": (
            f"Install via: https://github.com/rhysd/actionlint/releases "
            f"(v{versions['actionlint']}+)"
        ),
        "clippy": (
            f"Install via: rustup component add clippy "
            f"(requires Rust {versions['clippy']}+)"
        ),
        "rustfmt": (
            f"Install via: rustup component add rustfmt "
            f"(v{versions['rustfmt']}+)"
        ),
        "cargo_audit": (
            f"Install via: cargo install cargo-audit "
            f"(v{versions['cargo_audit']}+)"
        ),
        "semgrep": (
            f"Install via: pip install semgrep>="
            f"{versions['semgrep']} or brew install semgrep"
        ),
        "gitleaks": (
            f"Install via: https://github.com/gitleaks/gitleaks/releases "
            f"(v{versions['gitleaks']}+)"
        ),
        "shellcheck": (
            f"Install via: https://github.com/koalaman/shellcheck/releases "
            f"(v{versions['shellcheck']}+)"
        ),
        "shfmt": (
            f"Install via: https://github.com/mvdan/sh/releases "
            f"(v{versions['shfmt']}+)"
        ),
        "sqlfluff": (
            f"Install via: pip install sqlfluff>="
            f"{versions['sqlfluff']} "
            f"or uv add sqlfluff>={versions['sqlfluff']}"
        ),
        "taplo": (
            f"Install via: cargo install taplo-cli "
            f"or download from https://github.com/tamasfe/taplo/releases "
            f"(v{versions['taplo']}+)"
        ),
    }

    return hints
