#!/usr/bin/env python3
"""Generate documentation from pyproject.toml version requirements."""

import sys
from pathlib import Path

# Add the lintro package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lintro.tools.core.version_requirements import (
    get_install_hints,
    get_minimum_versions,
)


def generate_version_table() -> str:
    """Generate a Markdown table of tool versions.

    Returns:
        str: Markdown-formatted table string with tool version information.
    """
    versions = get_minimum_versions()

    # Separate bundled Python tools from external tools
    bundled_tools = {
        "ruff": "Fast Python linter and formatter",
        "black": "Python code formatter",
        "bandit": "Python security linter",
        "yamllint": "YAML linter",
        "pydoclint": "Python docstring linter",
    }

    external_tools = {
        "pytest": (
            "Python test framework",
            ("pip install pytest>={version} or uv add pytest>={version}"),
        ),
        "prettier": (
            "JavaScript/TypeScript formatter",
            "npm install --save-dev prettier>={version}",
        ),
        "oxlint": (
            "Fast JavaScript/TypeScript linter",
            "npm install --save-dev oxlint>={version}",
        ),
        "oxfmt": (
            "Fast JavaScript/TypeScript formatter",
            "npm install --save-dev oxfmt>={version}",
        ),
        "hadolint": (
            "Dockerfile linter",
            ("https://github.com/hadolint/hadolint/releases (v{version}+)"),
        ),
        "actionlint": (
            "GitHub Actions linter",
            ("https://github.com/rhysd/actionlint/releases (v{version}+)"),
        ),
    }

    # Generate bundled tools table
    bundled_table = "| Tool | Version | Purpose |\n|------|---------|---------|\n"
    for tool, description in bundled_tools.items():
        version = versions.get(tool, "unknown")
        bundled_table += f"| `{tool}` | {version} | {description} |\n"

    # Generate external tools table
    external_table = (
        "| Tool | Version | Installation |\n|------|---------|--------------|\n"
    )
    for tool, (_description, install_template) in external_tools.items():
        version = versions.get(tool, "unknown")
        install_cmd = install_template.format(version=version)
        external_table += f"| {tool.capitalize()} | ≥{version} | {install_cmd} |\n"

    return bundled_table + "\n" + external_table


def main() -> None:
    """Generate documentation and print to stdout."""
    print("=== Tool Version Requirements (Generated from pyproject.toml) ===")
    print()
    print("Bundled Python Tools:")
    print("---------------------")
    versions = get_minimum_versions()
    hints = get_install_hints()

    bundled_tools = ["ruff", "black", "bandit", "yamllint", "pydoclint"]
    for tool in bundled_tools:
        version = versions.get(tool, "unknown")
        print(f"- {tool}: {version}")

    print()
    print("External Tools:")
    print("---------------")
    external_tools = ["pytest", "prettier", "oxlint", "oxfmt", "hadolint", "actionlint"]
    for tool in external_tools:
        version = versions.get(tool, "unknown")
        hint = hints.get(tool, "").replace("Install via: ", "")
        print(f"- {tool}: ≥{version} ({hint})")

    print()
    print("=== Markdown Tables ===")
    print()
    print(generate_version_table())


if __name__ == "__main__":
    main()
