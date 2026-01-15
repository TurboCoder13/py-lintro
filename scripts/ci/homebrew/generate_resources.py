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
import re
import sys
from importlib.metadata import distributions

from packaging.requirements import Requirement
from pypi_utils import fetch_pypi_json, get_sdist_info

# Template for a single resource stanza
RESOURCE_TEMPLATE = """  resource "{name}" do
    url "{url}"
    sha256 "{sha256}"
  end
"""


def normalize_name(name: str) -> str:
    """Normalize package name per PEP 503.

    Args:
        name: Package name to normalize.

    Returns:
        Normalized package name (lowercase, runs of [-_.] replaced with single hyphen).
    """
    return re.sub(r"[-_.]+", "-", name.lower())


def build_distribution_map() -> dict[str, tuple[str, list[str] | None]]:
    """Build a cached map of all installed distributions.

    Returns:
        Dictionary mapping normalized package names to (version, requires) tuples.
    """
    dist_map: dict[str, tuple[str, list[str] | None]] = {}
    for dist in distributions():
        name = dist.metadata["Name"]
        version = dist.metadata["Version"]
        if name and version:
            normalized = normalize_name(name)
            requires = dist.metadata.get_all("Requires-Dist")
            dist_map[normalized] = (version, requires)
    return dist_map


def get_installed_packages() -> dict[str, str]:
    """Get all installed packages and their versions.

    Returns:
        Dictionary mapping normalized package names to versions.
    """
    dist_map = build_distribution_map()
    return {name: version for name, (version, _) in dist_map.items()}


def get_package_dependencies(package_name: str) -> set[str]:
    """Get all dependencies of a package recursively.

    Args:
        package_name: Name of the package to analyze.

    Returns:
        Set of normalized dependency package names.
    """
    # Build cached distribution map for O(n) lookup
    dist_map = build_distribution_map()

    # Normalize the input package name
    normalized_name = normalize_name(package_name)

    # Build the set of all dependencies
    dependencies: set[str] = set()
    to_process = {normalized_name}
    processed: set[str] = set()

    while to_process:
        current = to_process.pop()
        if current in processed:
            continue
        processed.add(current)

        # Look up package in cached distribution map (O(1) lookup)
        if current not in dist_map:
            continue

        _, requires = dist_map[current]
        if not requires:
            continue

        for req_str in requires:
            # Use packaging.Requirement for robust parsing
            try:
                req = Requirement(req_str)
                req_name = normalize_name(req.name)
                if req_name in dist_map:
                    dependencies.add(req_name)
                    to_process.add(req_name)
            except Exception:
                # Skip malformed requirements
                continue

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
    exclude: set[str] = {normalize_name(name) for name in args.exclude}

    # Always exclude the main package
    main_package = normalize_name(args.package)
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
