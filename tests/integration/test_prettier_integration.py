"""Integration tests for Prettier core."""

import subprocess
from pathlib import Path

import pytest
from loguru import logger

from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.tools.implementations.tool_prettier import PrettierTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = Path("test_samples/prettier_violations.js")


@pytest.fixture
def temp_prettier_file(tmp_path):
    temp_file = tmp_path / SAMPLE_FILE.name
    temp_file.write_text(SAMPLE_FILE.read_text())
    return temp_file


def run_prettier_directly(
    file_path: Path, check_only: bool = True
) -> tuple[bool, str, int]:
    """Run Prettier directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check/format.
        check_only: If True, use --check, else --write.

    Returns:
        tuple[bool, str, int]: Tuple of (success, output, issues_count).
    """
    cmd = PrettierTool()._get_executable_command("prettier") + [
        "prettier",
        "--check" if check_only else "--write",
        file_path.name,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=file_path.parent,
    )
    # Combine stdout and stderr for full output
    full_output = result.stdout + result.stderr
    # Count issues using the prettier parser (handles ANSI codes properly)
    issues = parse_prettier_output(full_output)
    issues_count = len(issues)
    success = (
        result.returncode == 0 and issues_count == 0
        if check_only
        else result.returncode == 0
    )
    return success, full_output, issues_count


def test_prettier_reports_violations_direct(temp_prettier_file):
    """Prettier CLI: Should detect and report violations in a sample file.

    Args:
        temp_prettier_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running Prettier directly on sample file...")
    success, output, issues = run_prettier_directly(temp_prettier_file, check_only=True)
    logger.info(f"[LOG] Prettier found {issues} issues. Output:\n{output}")
    assert not success, "Prettier should fail when violations are present."
    assert issues > 0, "Prettier should report at least one issue."
    # Check for warning indicators (handles both plain and ANSI-coded output)
    has_warnings = "[warn]" in output or "warn" in output
    assert has_warnings, "Prettier output should contain warning indicators."


def test_prettier_reports_violations_through_lintro(temp_prettier_file):
    """Lintro PrettierTool: Should detect and report violations in a sample file.

    Args:
        temp_prettier_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running PrettierTool through lintro on sample file...")
    tool = PrettierTool()
    tool.set_options()
    result = tool.check([str(temp_prettier_file)])
    logger.info(
        f"[LOG] Lintro PrettierTool found {result.issues_count} issues. "
        f"Output:\n{result.output}"
    )
    assert not result.success, (
        "Lintro PrettierTool should fail when violations are present."
    )
    assert result.issues_count > 0, (
        "Lintro PrettierTool should report at least one issue."
    )
    # Check for warning indicators (handles both plain and ANSI-coded output)
    has_warnings = "[warn]" in result.output or "warn" in result.output
    assert has_warnings, "Lintro PrettierTool output should contain warning indicators."


def test_prettier_fix_method(temp_prettier_file):
    """Lintro PrettierTool: Should fix formatting issues.

    Args:
        temp_prettier_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running PrettierTool.fix() on sample file...")
    tool = PrettierTool()
    tool.set_options()

    # Check before fixing
    pre_result = tool.check([str(temp_prettier_file)])
    logger.info(
        f"[LOG] Before fix: {pre_result.issues_count} issues. "
        f"Output:\n{pre_result.output}"
    )
    assert not pre_result.success, "Should have issues before fixing"
    assert pre_result.issues_count > 0, "Should have issues before fixing"

    # Fix issues
    post_result = tool.fix([str(temp_prettier_file)])
    logger.info(
        f"[LOG] After fix: {post_result.issues_count} issues. "
        f"Output:\n{post_result.output}"
    )
    assert post_result.success, "Should fix all issues"
    assert post_result.issues_count == 0, "Should fix all issues"

    # Verify no issues remain
    final_result = tool.check([str(temp_prettier_file)])
    logger.info(
        f"[LOG] Final check: {final_result.issues_count} issues. "
        f"Output:\n{final_result.output}"
    )
    assert final_result.success, "Should have no issues after fixing"
    assert final_result.issues_count == 0, "Should have no issues after fixing"


def test_prettier_output_consistency_direct_vs_lintro(temp_prettier_file):
    """Prettier CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        temp_prettier_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Comparing prettier CLI and Lintro PrettierTool outputs...")
    tool = PrettierTool()
    tool.set_options()

    # Run prettier directly
    direct_success, direct_output, direct_issues = run_prettier_directly(
        temp_prettier_file, check_only=True
    )

    # Run through lintro
    result = tool.check([str(temp_prettier_file)])

    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}"
    )
    assert direct_success == result.success, (
        "Success/failure mismatch between CLI and Lintro."
    )
    assert direct_issues == result.issues_count, (
        f"Issue count mismatch: CLI={direct_issues}, Lintro={result.issues_count}\n"
        f"CLI Output:\n{direct_output}\nLintro Output:\n{result.output}"
    )
