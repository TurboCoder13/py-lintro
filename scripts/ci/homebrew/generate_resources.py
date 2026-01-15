#!/usr/bin/env python3
"""Generate Homebrew resource stanzas for Python package dependencies.

This is a modern replacement for homebrew-pypi-poet that:
- Uses importlib.metadata instead of deprecated pkg_resources
- Uses pypi.org API directly (via pypi_utils)
- Generates resource stanzas compatible with Homebrew formulae

Usage:
    # Generate resources for a package installed in current environment
    python3 generate_resources.py lintro

    # Exclude specific packages (e.g., already available as Homebrew formulae)
    python3 generate_resources.py lintro --exclude bandit black mypy ruff yamllint
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import distributions

from pypi_utils import fetch_pypi_json, get_sdist_info

# Template for a single resource stanza
RESOURCE_TEMPLATE = """  resource "{name}" do
    url "{url}"
    sha256 "{sha256}"
  end
"""


def get_installed_packages() -> dict[str, str]:
    """Get all installed packages and their versions.

    Returns:
        Dictionary mapping normalized package names to versions.
    """
    packages: dict[str, str] = {}
    for dist in distributions():
        name = dist.metadata["Name"]
        version = dist.metadata["Version"]
        if name and version:
            # Normalize package name (lowercase, replace underscores with hyphens)
            normalized = name.lower().replace("_", "-")
            packages[normalized] = version
    return packages


def get_package_dependencies(package_name: str) -> set[str]:
    """Get all dependencies of a package recursively.

    Args:
        package_name: Name of the package to analyze.

    Returns:
        Set of normalized dependency package names.
    """
    # Get all installed packages for lookup
    installed = get_installed_packages()

    # Normalize the input package name
    normalized_name = package_name.lower().replace("_", "-")

    # Build the set of all dependencies
    dependencies: set[str] = set()
    to_process = {normalized_name}
    processed: set[str] = set()

    while to_process:
        current = to_process.pop()
        if current in processed:
            continue
        processed.add(current)

        # Find this package in installed distributions
        for dist in distributions():
            dist_name = dist.metadata["Name"]
            if dist_name and dist_name.lower().replace("_", "-") == current:
                # Add this package's direct dependencies
                requires = dist.metadata.get_all("Requires-Dist") or []
                for req in requires:
                    # Parse requirement (e.g., "click>=7.0" -> "click")
                    # Handle extras like "package[extra]"
                    req_name = req.split(";")[0].split("[")[0].split(">=")[0]
                    req_name = req_name.split("<=")[0].split("==")[0].split("!=")[0]
                    req_name = req_name.split("<")[0].split(">")[0].split("~=")[0]
                    req_name = req_name.strip().lower().replace("_", "-")
                    if req_name and req_name in installed:
                        dependencies.add(req_name)
                        to_process.add(req_name)
                break

    # Don't include the main package itself
    dependencies.discard(normalized_name)
    return dependencies


def generate_resource_stanza(
    package_name: str,
    version: str,
) -> str | None:
    """Generate a Homebrew resource stanza for a package.

    Args:
        package_name: Package name on PyPI.
        version: Package version.

    Returns:
        Resource stanza string, or None if sdist not available.
    """
    try:
        data = fetch_pypi_json(package_name, version)
        info = get_sdist_info(data)
        return RESOURCE_TEMPLATE.format(
            name=package_name,
            url=info.tarball_url,
            sha256=info.tarball_sha256,
        )
    except SystemExit:
        # get_sdist_info calls sys.exit if no sdist found
        print(
            f"Warning: No sdist for {package_name}=={version}, skipping",
            file=sys.stderr,
        )
        return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Homebrew resource stanzas for Python dependencies",
    )
    parser.add_argument(
        "package",
        help="Package name to generate resources for",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Package names to exclude (e.g., available as Homebrew formulae)",
    )
    args = parser.parse_args()

    # Normalize exclusion list
    exclude: set[str] = {name.lower().replace("_", "-") for name in args.exclude}

    # Always exclude the main package
    main_package = args.package.lower().replace("_", "-")
    exclude.add(main_package)

    # Get installed packages and their versions
    installed = get_installed_packages()

    # Get all dependencies
    dependencies = get_package_dependencies(args.package)

    # Filter out excluded packages
    to_generate = sorted(dependencies - exclude)

    if not to_generate:
        print("No dependencies to generate resources for", file=sys.stderr)
        sys.exit(1)

    # Generate resource stanzas
    stanzas: list[str] = []
    for dep in to_generate:
        version = installed.get(dep)
        if not version:
            print(f"Warning: {dep} not found in installed packages", file=sys.stderr)
            continue

        stanza = generate_resource_stanza(dep, version)
        if stanza:
            stanzas.append(stanza)

    # Output all stanzas
    print("\n".join(stanzas))


if __name__ == "__main__":
    main()
