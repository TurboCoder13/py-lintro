"""Integration tests for darglint core."""

import shutil
import subprocess
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.plugins import ToolRegistry

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = "test_samples/tools/python/darglint/darglint_violations.py"


def run_darglint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run darglint directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with darglint.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    cmd = [
        "darglint",
        "--strictness",
        "full",
        "--verbosity",
        "2",
        file_path.name,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=file_path.parent,
    )
    issues = [
        line for line in result.stdout.splitlines() if ":" in line and "DAR" in line
    ]
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return success, result.stdout, issues_count


def _ensure_darglint_cli_available() -> None:
    """Skip test if darglint CLI is not runnable.

    Attempts to execute `darglint --version` to verify that the CLI exists
    and is runnable in the current environment. Some installations may have
    an entrypoint present but an invalid shebang, which raises ENOENT on exec.
    """
    try:
        subprocess.run(
            ["darglint", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("darglint CLI not installed/runnable; skipping direct CLI test")


def test_darglint_reports_violations_direct(tmp_path: Path) -> None:
    """Darglint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    _ensure_darglint_cli_available()
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Running darglint directly on sample file...")
    success, output, issues = run_darglint_directly(sample_file)
    logger.info(f"[LOG] Darglint found {issues} issues. Output:\n{output}")
    assert_that(success).is_false().described_as(
        "Darglint should fail when violations are present.",
    )
    assert_that(issues).is_greater_than(0).described_as(
        "Darglint should report at least one issue.",
    )
    assert_that(output).contains("DAR").described_as(
        "Darglint output should contain error codes.",
    )


def test_darglint_reports_violations_through_lintro(tmp_path: Path) -> None:
    """Lintro DarglintTool: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    _ensure_darglint_cli_available()
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(f"SAMPLE_FILE: {sample_file}, exists: {sample_file.exists()}")
    logger.info("[TEST] Running DarglintTool through lintro on sample file...")
    tool = ToolRegistry.get("darglint")
    tool.set_options(strictness="full", verbosity=2)
    result = tool.check([str(sample_file)], {})
    logger.info(
        f"[LOG] Lintro DarglintTool found {result.issues_count} issues. "
        f"Output:\n{result.output}",
    )
    assert_that(result.success).is_false().described_as(
        "Lintro DarglintTool should fail when violations are present.",
    )
    assert_that(result.issues_count).is_greater_than(0).described_as(
        "Lintro DarglintTool should report at least one issue.",
    )
    assert_that(result.output).contains("DAR").described_as(
        "Lintro DarglintTool output should contain error codes.",
    )


def test_darglint_output_consistency_direct_vs_lintro(tmp_path: Path) -> None:
    """Darglint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    _ensure_darglint_cli_available()
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Comparing darglint CLI and Lintro DarglintTool outputs...")
    tool = ToolRegistry.get("darglint")
    tool.set_options(strictness="full", verbosity=2)
    direct_success, direct_output, direct_issues = run_darglint_directly(sample_file)
    result = tool.check([str(sample_file)], {})
    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}",
    )
    assert_that(direct_success).is_equal_to(result.success).described_as(
        "Success/failure mismatch between CLI and Lintro.",
    )
    assert_that(direct_issues).is_equal_to(result.issues_count).described_as(
        "Issue count mismatch between CLI and Lintro.",
    )
    # Optionally compare error codes if output format is stable


def test_darglint_fix_method_not_implemented(tmp_path: Path) -> None:
    """Lintro DarglintTool: .fix() should raise NotImplementedError.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(
        "[TEST] Verifying that DarglintTool.fix() raises NotImplementedError...",
    )
    tool = ToolRegistry.get("darglint")
    with pytest.raises(NotImplementedError):
        tool.fix([str(sample_file)], {})
    logger.info("[LOG] NotImplementedError correctly raised by DarglintTool.fix().")
