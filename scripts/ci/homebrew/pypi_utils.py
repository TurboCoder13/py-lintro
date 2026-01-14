#!/usr/bin/env python3
"""Shared PyPI API utilities for Homebrew formula generation."""

import json
import sys
import urllib.request
from typing import NamedTuple


class PackageInfo(NamedTuple):
    """Information about a package release."""

    version: str
    tarball_url: str
    tarball_sha256: str


class WheelInfo(NamedTuple):
    """Information about a wheel file."""

    url: str
    sha256: str


def fetch_pypi_json(package: str, version: str | None = None) -> dict:
    """Fetch package JSON from PyPI.

    Args:
        package: Package name on PyPI.
        version: Specific version to fetch, or None for latest.

    Returns:
        PyPI JSON response as dictionary.

    Raises:
        SystemExit: If the request fails.
    """
    if version:
        url = f"https://pypi.org/pypi/{package}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{package}/json"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)


def get_latest_version(package: str) -> str:
    """Get the latest version of a package from PyPI.

    Args:
        package: Package name on PyPI.

    Returns:
        Latest version string.
    """
    data = fetch_pypi_json(package)
    return data["info"]["version"]


def get_sdist_info(data: dict) -> PackageInfo:
    """Extract source distribution info from PyPI JSON.

    Args:
        data: PyPI JSON response.

    Returns:
        PackageInfo with version, tarball URL, and SHA256.

    Raises:
        SystemExit: If no sdist is found.
    """
    version = data["info"]["version"]
    for url_info in data.get("urls", []):
        if url_info.get("packagetype") == "sdist":
            return PackageInfo(
                version=version,
                tarball_url=url_info["url"],
                tarball_sha256=url_info["digests"]["sha256"],
            )

    print("Error: No source distribution found", file=sys.stderr)
    sys.exit(1)


def find_universal_wheel(data: dict) -> WheelInfo | None:
    """Find a universal wheel (py3-none-any).

    Args:
        data: PyPI JSON response.

    Returns:
        WheelInfo if found, None otherwise.
    """
    for url_info in data.get("urls", []):
        if "py3-none-any.whl" in url_info.get("filename", ""):
            return WheelInfo(
                url=url_info["url"],
                sha256=url_info["digests"]["sha256"],
            )
    return None


def find_macos_wheel(data: dict, arch: str) -> WheelInfo | None:
    """Find a macOS wheel for specific architecture.

    Args:
        data: PyPI JSON response.
        arch: Architecture string (e.g., "arm64", "x86_64").

    Returns:
        WheelInfo if found, None otherwise.
    """
    for url_info in data.get("urls", []):
        filename = url_info.get("filename", "")
        if "cp313-cp313-macosx" in filename and arch in filename:
            return WheelInfo(
                url=url_info["url"],
                sha256=url_info["digests"]["sha256"],
            )
    return None
