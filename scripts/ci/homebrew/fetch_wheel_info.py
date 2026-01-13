#!/usr/bin/env python3
"""Fetch wheel information from PyPI for Homebrew formula generation."""

import argparse
import json
import sys
import urllib.request
from typing import NamedTuple


class WheelInfo(NamedTuple):
    """Information about a wheel file."""

    url: str
    sha256: str


def fetch_pypi_json(package: str) -> dict:
    """Fetch package JSON from PyPI."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)


def find_universal_wheel(data: dict) -> WheelInfo | None:
    """Find a universal wheel (py3-none-any)."""
    for url_info in data.get("urls", []):
        if "py3-none-any.whl" in url_info.get("filename", ""):
            return WheelInfo(
                url=url_info["url"],
                sha256=url_info["digests"]["sha256"],
            )
    return None


def find_macos_wheel(data: dict, arch: str) -> WheelInfo | None:
    """Find a macOS wheel for specific architecture."""
    for url_info in data.get("urls", []):
        filename = url_info.get("filename", "")
        if "cp313-cp313-macosx" in filename and arch in filename:
            return WheelInfo(
                url=url_info["url"],
                sha256=url_info["digests"]["sha256"],
            )
    return None


def generate_universal_resource(package: str, wheel: WheelInfo, comment: str) -> str:
    """Generate Homebrew resource stanza for universal wheel."""
    return f'''  # {comment}
  resource "{package}" do
    url "{wheel.url}"
    sha256 "{wheel.sha256}"
  end'''


def generate_platform_resource(
    package: str,
    arm_wheel: WheelInfo,
    intel_wheel: WheelInfo,
    comment: str,
) -> str:
    """Generate Homebrew resource stanza for platform-specific wheels."""
    return f'''  # {comment}
  resource "{package}" do
    on_arm do
      url "{arm_wheel.url}"
      sha256 "{arm_wheel.sha256}"
    end
    on_intel do
      url "{intel_wheel.url}"
      sha256 "{intel_wheel.sha256}"
    end
  end'''


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fetch wheel info from PyPI")
    parser.add_argument("package", help="Package name")
    parser.add_argument(
        "--type",
        choices=["universal", "platform"],
        default="universal",
        help="Wheel type to fetch",
    )
    parser.add_argument(
        "--comment",
        default="",
        help="Comment to add above resource stanza",
    )
    args = parser.parse_args()

    data = fetch_pypi_json(args.package)

    if args.type == "universal":
        wheel = find_universal_wheel(data)
        if not wheel:
            print(f"Error: No universal wheel found for {args.package}", file=sys.stderr)
            sys.exit(1)
        comment = args.comment or f"{args.package} - using wheel"
        print(generate_universal_resource(args.package, wheel, comment))
    else:
        arm_wheel = find_macos_wheel(data, "arm64")
        intel_wheel = find_macos_wheel(data, "x86_64")
        if not arm_wheel or not intel_wheel:
            print(
                f"Error: Missing platform wheels for {args.package}",
                file=sys.stderr,
            )
            print(f"  arm64: {'found' if arm_wheel else 'missing'}", file=sys.stderr)
            print(f"  x86_64: {'found' if intel_wheel else 'missing'}", file=sys.stderr)
            sys.exit(1)
        comment = args.comment or f"{args.package} - using platform-specific wheels"
        print(generate_platform_resource(args.package, arm_wheel, intel_wheel, comment))


if __name__ == "__main__":
    main()
