"""Pytest configuration for gitleaks integration tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml.

    Returns:
        Path to the project root directory.
    """
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return path.parent.parent.parent.parent.parent  # fallback


# Paths to test samples
SAMPLE_DIR = _find_project_root() / "test_samples"
GITLEAKS_SAMPLES = SAMPLE_DIR / "tools" / "security" / "gitleaks"
CLEAN_SAMPLE = GITLEAKS_SAMPLES / "gitleaks_clean.py"

# Violation content generated at runtime to avoid triggering secret scanners
# These patterns are designed to trigger gitleaks detection rules:
# - aws-access-token: AKIA prefix + 16 chars from [A-Z2-7]
# - github-pat: ghp_ prefix + 36 alphanumeric chars
# - private-key: RSA private key header
_VIOLATION_CONTENT = '''# Generated test file with fake secrets for gitleaks testing
# WARNING: These are FAKE credentials for testing purposes only!

# AWS Access Key pattern (triggers aws-access-token rule)
AWS_ACCESS_KEY = "AKIA''' + "Z7QRSTUVWXY23456" + '''"

# GitHub PAT pattern (triggers github-pat rule)
GITHUB_TOKEN = "ghp_''' + "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8" + '''"

# Private key pattern (triggers private-key rule)
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBALRiMLAHudeSA2ai2TuYkPk
-----END RSA PRIVATE KEY-----"""
'''


@pytest.fixture
def gitleaks_violation_file(tmp_path: Path) -> str:
    """Generate a file with fake secrets at runtime for gitleaks testing.

    This generates the file at runtime rather than copying from a static file
    to avoid triggering secret scanners in CI/CD pipelines.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the generated file as a string.
    """
    dst = tmp_path / "gitleaks_violations.py"
    dst.write_text(_VIOLATION_CONTENT)
    return str(dst)


@pytest.fixture
def gitleaks_clean_file(tmp_path: Path) -> str:
    """Copy the gitleaks clean sample to a temp directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path to the copied file as a string.
    """
    dst = tmp_path / "gitleaks_clean.py"
    shutil.copy(CLEAN_SAMPLE, dst)
    return str(dst)
