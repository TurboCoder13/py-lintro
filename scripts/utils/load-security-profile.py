#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Load security profile endpoints from centralized configuration.

This script reads .github/data/security-config.yml and outputs
endpoints for a given security profile in GitHub Actions format.
"""

import sys
from pathlib import Path

import yaml


def load_security_profile(profile_name: str, config_file: Path) -> str:
    """Load endpoints for a security profile from configuration file.

    Args:
        profile_name: Security profile to load (e.g., 'python_workflow')
        config_file: Path to security-config.yml

    Returns:
        Endpoints string in GitHub Actions format (endpoints=space-separated-list)
    """
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_file}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in configuration file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate profile exists
    if profile_name not in config.get("profiles", {}):
        print(
            f'❌ Security profile "{profile_name}" not found in configuration',
            file=sys.stderr,
        )
        sys.exit(1)

    profile_config = config["profiles"][profile_name]
    endpoint_groups = profile_config.get("endpoints", [])

    if not endpoint_groups:
        print(
            f'❌ No endpoint groups defined for profile "{profile_name}"',
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect endpoints from all groups
    all_endpoints = set()
    for group in endpoint_groups:
        if group not in config.get("endpoints", {}):
            print(
                f'❌ Endpoint group "{group}" not found in configuration',
                file=sys.stderr,
            )
            sys.exit(1)
        endpoints = config["endpoints"][group]
        all_endpoints.update(endpoints)

    # Return in GitHub Actions format
    endpoints_str = " ".join(sorted(all_endpoints))
    return f"endpoints={endpoints_str}"


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PROFILE_NAME", file=sys.stderr)
        print(
            "Load endpoints for security profile from .github/data/security-config.yml",
            file=sys.stderr,
        )
        sys.exit(1)

    profile_name = sys.argv[1]
    config_file = Path(".github/data/security-config.yml")

    result = load_security_profile(profile_name, config_file)
    print(result)


if __name__ == "__main__":
    main()
