#!/usr/bin/env python3
"""Fetch package information from PyPI for Homebrew formula generation.

Usage:
    # Get tarball URL and SHA256 for a specific version
    python3 fetch_package_info.py lintro 1.0.0

    # Get latest version
    python3 fetch_package_info.py lintro --latest

    # Output as shell variables for sourcing
    python3 fetch_package_info.py lintro 1.0.0 --shell
"""

import argparse
import sys

from pypi_utils import fetch_pypi_json, get_latest_version, get_sdist_info


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch package info from PyPI",
    )
    parser.add_argument("package", help="Package name")
    parser.add_argument(
        "version",
        nargs="?",
        help="Package version (omit with --latest)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Get latest version only",
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Output as shell variable assignments",
    )
    args = parser.parse_args()

    if args.latest:
        version = get_latest_version(args.package)
        print(version)
        return

    if not args.version:
        print("Error: version required (or use --latest)", file=sys.stderr)
        sys.exit(1)

    data = fetch_pypi_json(args.package, args.version)
    info = get_sdist_info(data)

    if args.shell:
        print(f'TARBALL_URL="{info.tarball_url}"')
        print(f'TARBALL_SHA="{info.tarball_sha256}"')
        print(f'VERSION="{info.version}"')
    else:
        print(info.tarball_url)
        print(info.tarball_sha256)


if __name__ == "__main__":
    main()
