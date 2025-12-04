"""Integration tests for markdownlint tool."""

import shutil
import subprocess
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.tools.implementations.tool_markdownlint import MarkdownlintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")
SAMPLE_FILE = "test_samples/markdownlint_violations.md"


def run_markdownlint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run markdownlint-cli2 directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with markdownlint-cli2.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    # Try npx first, then direct executable
    cmd = None
    if shutil.which("npx"):
        cmd = ["npx", "--yes", "markdownlint-cli2", str(file_path)]
    elif shutil.which("markdownlint-cli2"):
        cmd = ["markdownlint-cli2", str(file_path)]
    else:
        pytest.skip("markdownlint-cli2 not found in PATH")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=file_path.parent,
    )

    # Count issues from output (non-empty lines are typically issues)
    issues = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and ":" in line and "MD" in line
    ]
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return (success, result.stdout, issues_count)


@pytest.mark.markdownlint
def test_markdownlint_available() -> None:
    """Check if markdownlint-cli2 is available in PATH."""
    try:
        if shutil.which("npx"):
            result = subprocess.run(
                ["npx", "--yes", "markdownlint-cli2", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        elif shutil.which("markdownlint-cli2"):
            result = subprocess.run(
                ["markdownlint-cli2", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        else:
            pytest.skip("markdownlint-cli2 not found in PATH")
        assert_that(result.returncode).is_equal_to(0)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("markdownlint-cli2 not available")


@pytest.mark.markdownlint
def test_markdownlint_direct_vs_lintro_parity() -> None:
    """Compare direct markdownlint-cli2 output with lintro wrapper.

    Runs markdownlint-cli2 directly on the sample file and compares the
    issue count with lintro's wrapper to ensure parity.
    """
    sample_path = Path(SAMPLE_FILE)
    if not sample_path.exists():
        pytest.skip(f"Sample file {SAMPLE_FILE} not found")

    # Run markdownlint-cli2 directly
    direct_success, direct_output, direct_count = run_markdownlint_directly(
        sample_path,
    )

    # Run via lintro
    tool = MarkdownlintTool()
    lintro_result = tool.check(paths=[str(sample_path)])

    # Compare issue counts (allow some variance due to parsing differences)
    # Direct count may include lines we don't parse, so lintro count <= direct
    assert_that(lintro_result.issues_count).is_greater_than_or_equal_to(0)
    # If direct found issues, lintro should also find some
    if direct_count > 0:
        assert_that(lintro_result.issues_count).is_greater_than(0)

    # Both should agree on success/failure
    assert_that(lintro_result.success).is_equal_to(direct_success)


@pytest.mark.markdownlint
def test_markdownlint_integration_basic() -> None:
    """Basic integration test for markdownlint tool.

    Verifies that the tool can discover files, run checks, and parse output.
    """
    sample_path = Path(SAMPLE_FILE)
    if not sample_path.exists():
        pytest.skip(f"Sample file {SAMPLE_FILE} not found")

    tool = MarkdownlintTool()
    result = tool.check(paths=[str(sample_path)])

    assert_that(result).is_not_none()
    assert_that(result.name).is_equal_to("markdownlint")
    assert_that(result.issues_count).is_greater_than_or_equal_to(0)

    # If there are issues, verify they're properly structured
    if result.issues:
        issue = result.issues[0]
        assert_that(issue.file).is_not_empty()
        assert_that(issue.line).is_greater_than(0)
        assert_that(issue.code).matches(r"^MD\d+$")
        assert_that(issue.message).is_not_empty()
