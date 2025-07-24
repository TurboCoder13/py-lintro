"""Integration tests for darglint core."""

import shutil
import subprocess
from pathlib import Path

import pytest
from loguru import logger

from lintro.tools.implementations.tool_darglint import DarglintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = "test_samples/darglint_violations.py"


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


def test_darglint_reports_violations_direct(tmp_path):
    """Darglint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Running darglint directly on sample file...")
    success, output, issues = run_darglint_directly(sample_file)
    logger.info(f"[LOG] Darglint found {issues} issues. Output:\n{output}")
    assert not success, "Darglint should fail when violations are present."
    assert issues > 0, "Darglint should report at least one issue."
    assert "DAR" in output, "Darglint output should contain error codes."


def test_darglint_reports_violations_through_lintro(tmp_path):
    """Lintro DarglintTool: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(f"SAMPLE_FILE: {sample_file}, exists: {sample_file.exists()}")
    logger.info("[TEST] Running DarglintTool through lintro on sample file...")
    tool = DarglintTool()
    tool.set_options(strictness="full", verbosity=2)
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] Lintro DarglintTool found {result.issues_count} issues. Output:\n{result.output}"
    )
    assert not result.success, (
        "Lintro DarglintTool should fail when violations are present."
    )
    assert result.issues_count > 0, (
        "Lintro DarglintTool should report at least one issue."
    )
    assert "DAR" in result.output, (
        "Lintro DarglintTool output should contain error codes."
    )


def test_darglint_output_consistency_direct_vs_lintro(tmp_path):
    """Darglint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Comparing darglint CLI and Lintro DarglintTool outputs...")
    tool = DarglintTool()
    tool.set_options(strictness="full", verbosity=2)
    direct_success, direct_output, direct_issues = run_darglint_directly(sample_file)
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}"
    )
    assert direct_success == result.success, (
        "Success/failure mismatch between CLI and Lintro."
    )
    assert direct_issues == result.issues_count, (
        "Issue count mismatch between CLI and Lintro."
    )
    # Optionally compare error codes if output format is stable


def test_darglint_fix_method_not_implemented(tmp_path):
    """Lintro DarglintTool: .fix() should raise NotImplementedError.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    sample_file = tmp_path / "darglint_violations.py"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(
        "[TEST] Verifying that DarglintTool.fix() raises NotImplementedError..."
    )
    tool = DarglintTool()
    with pytest.raises(NotImplementedError):
        tool.fix([str(sample_file)])
    logger.info("[LOG] NotImplementedError correctly raised by DarglintTool.fix().")
