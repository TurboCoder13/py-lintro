"""Tests for shell scripts in the scripts/ directory.

This module tests the shell scripts to ensure they follow best practices,
have correct syntax, and provide appropriate help/usage information.
"""

import subprocess
from pathlib import Path

from assertpy import assert_that


def test_detect_changes_help() -> None:
    """detect-changes.sh should provide help and exit 0."""
    script_path = Path("scripts/ci/detect-changes.sh").resolve()
    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert_that(result.returncode).is_equal_to(0)
    assert_that(result.stdout).contains("Usage:")


def test_renovate_regex_manager_current_value() -> None:
    """Ensure Renovate custom managers use currentValue to satisfy schema."""
    config_path = Path("renovate.json")
    content = config_path.read_text()
    assert_that(content).contains("customManagers")
    assert_that(content).contains("currentValue")
