#!/usr/bin/env python3
"""Extract coverage percentage from coverage.xml file."""

import xml.etree.ElementTree as ET
import sys
import os


def extract_coverage_percentage():
    """Extract coverage percentage from coverage.xml file."""
    coverage_file = "coverage.xml"

    # Debug: Check what files are available
    print(f"Current directory: {os.getcwd()}")
    print("Files in current directory:")
    for file in os.listdir("."):
        if os.path.isfile(file):
            size = os.path.getsize(file)
            print(f"  {file} ({size} bytes)")
    print()

    if not os.path.exists(coverage_file):
        print(f"Coverage XML file '{coverage_file}' not found")
        print("percentage=0.0")
        return

    try:
        print("Coverage XML file found, extracting percentage...")
        print(f"Coverage XML file size: {os.path.getsize(coverage_file)} bytes")

        # Read and parse the XML file
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        print(f"XML root tag: {root.tag}")
        print(f"XML root attributes: {root.attrib}")

        # Look for coverage data at root level first (most common)
        root_line_rate = root.get("line-rate", "0")
        print(f"Root line-rate={root_line_rate}")
        if root_line_rate != "0":
            percentage = float(root_line_rate) * 100
            print(f"percentage={percentage:.1f}")
            return

        # Fallback: check packages
        packages = root.findall(".//package")
        print(f"Found {len(packages)} packages")

        for i, package in enumerate(packages):
            line_rate = package.get("line-rate", "0")
            print(f"Package {i}: line-rate={line_rate}")
            if line_rate != "0":
                percentage = float(line_rate) * 100
                print(f"percentage={percentage:.1f}")
                return

        # If still no coverage found, use root as fallback
        print("No coverage found in packages, using root as fallback")
        percentage = float(root_line_rate) * 100
        print(f"percentage={percentage:.1f}")

    except Exception as e:
        print(f"Error parsing coverage.xml: {e}", file=sys.stderr)
        print("percentage=0.0")


if __name__ == "__main__":
    extract_coverage_percentage()
