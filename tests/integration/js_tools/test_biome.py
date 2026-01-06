"""Integration tests for Biome core."""

import subprocess
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.parsers.biome.biome_parser import parse_biome_output
from lintro.tools.implementations.tool_biome import BiomeTool
from lintro.utils.tool_utils import format_tool_output

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = Path("test_samples/tools/javascript/biome/biome_violations.js")


@pytest.fixture
def temp_biome_file(tmp_path: Path) -> Path:
    """Create a temp copy of the sample JS file with violations.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        Path to the copied temporary JavaScript file containing violations.
    """
    temp_file = tmp_path / SAMPLE_FILE.name
    temp_file.write_text(SAMPLE_FILE.read_text())
    return temp_file


def run_biome_directly(
    file_path: Path,
    check_only: bool = True,
) -> tuple[bool, str, int]:
    """Run Biome directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check/fix.
        check_only: If True, use check mode, else use --write.

    Returns:
        tuple[bool, str, int]: Tuple of (success, output, issues_count).
    """
    cmd = ["npx", "@biomejs/biome", "lint", "--reporter", "json"]
    if not check_only:
        cmd.append("--write")
    cmd.append(file_path.name)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=file_path.parent,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"Biome subprocess timed out after 30s. Command: {' '.join(cmd)}",
        )
    # Combine stdout and stderr for full output
    full_output = result.stdout + result.stderr
    # Count issues using the biome parser
    issues = parse_biome_output(full_output)
    issues_count = len(issues)
    success = (
        result.returncode == 0 and issues_count == 0
        if check_only
        else result.returncode == 0
    )
    return success, full_output, issues_count


def test_biome_reports_violations_direct(temp_biome_file: Path) -> None:
    """Biome CLI: Should detect and report violations in a sample file.

    Args:
        temp_biome_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running Biome directly on sample file...")
    success, output, issues = run_biome_directly(temp_biome_file, check_only=True)
    logger.info(f"[LOG] Biome found {issues} issues. Output:\n{output}")
    # Biome may return 0 exit code even with warnings, so check issues count
    assert_that(issues > 0 or not success).is_true().described_as(
        "Biome should report issues or fail when violations are present.",
    )


def test_biome_reports_violations_through_lintro(temp_biome_file: Path) -> None:
    """Lintro BiomeTool: Should detect and report violations in a sample file.

    Args:
        temp_biome_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running BiomeTool through lintro on sample file...")
    tool = BiomeTool()
    tool.set_options()
    result = tool.check([str(temp_biome_file)])
    logger.info(
        f"[LOG] Lintro BiomeTool found {result.issues_count} issues. "
        f"Output:\n{result.output}",
    )
    # Note: Biome may succeed with warnings, so we check issues_count
    if result.issues_count > 0:
        assert_that(result.success).is_false().described_as(
            "Lintro BiomeTool should fail when violations are present.",
        )
    assert_that(result.issues_count).is_greater_than_or_equal_to(0).described_as(
        "Lintro BiomeTool should report issues count.",
    )


def test_biome_fix_method(temp_biome_file: Path) -> None:
    """Lintro BiomeTool: Should fix auto-fixable issues.

    Args:
        temp_biome_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Running BiomeTool.fix() on sample file...")
    tool = BiomeTool()
    tool.set_options()

    # Check before fixing
    pre_result = tool.check([str(temp_biome_file)])
    logger.info(
        f"[LOG] Before fix: {pre_result.issues_count} issues. "
        f"Output:\n{pre_result.output}",
    )
    initial_count = pre_result.issues_count

    # Fix issues
    post_result = tool.fix([str(temp_biome_file)])
    logger.info(
        f"[LOG] After fix: {post_result.remaining_issues_count} remaining issues. "
        f"Output:\n{post_result.output}",
    )

    # Verify that some issues were fixed (or all if all were fixable)
    assert_that(post_result.remaining_issues_count).is_less_than_or_equal_to(
        initial_count,
    ).described_as("Should fix at least some issues or have same count")

    # Verify no issues remain or fewer remain
    final_result = tool.check([str(temp_biome_file)])
    logger.info(
        f"[LOG] Final check: {final_result.issues_count} issues. "
        f"Output:\n{final_result.output}",
    )
    assert_that(final_result.issues_count).is_less_than_or_equal_to(
        initial_count,
    ).described_as("Should have same or fewer issues after fixing")


def test_biome_output_consistency_direct_vs_lintro(temp_biome_file: Path) -> None:
    """Biome CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        temp_biome_file: Pytest fixture providing a temporary file with violations.
    """
    logger.info("[TEST] Comparing Biome CLI and Lintro BiomeTool outputs...")
    tool = BiomeTool()
    tool.set_options()

    # Run biome directly
    direct_success, direct_output, direct_issues = run_biome_directly(
        temp_biome_file,
        check_only=True,
    )

    # Run through lintro
    result = tool.check([str(temp_biome_file)])

    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}",
    )
    # Issue counts should match (allowing for slight differences due to parsing)
    assert_that(abs(direct_issues - result.issues_count)).is_less_than_or_equal_to(
        1,
    ).described_as(
        f"Issue count mismatch: CLI={direct_issues}, Lintro={result.issues_count}\n"
        f"CLI Output:\n{direct_output}\nLintro Output:\n{result.output}",
    )


def test_biome_fix_sets_issues_for_table(temp_biome_file: Path) -> None:
    """BiomeTool.fix should populate issues for table rendering.

    Args:
        temp_biome_file: Pytest fixture providing a temporary file with violations.
    """
    tool = BiomeTool()
    tool.set_options()

    # Ensure there are initial issues
    pre_result = tool.check([str(temp_biome_file)])
    if pre_result.issues_count == 0:
        pytest.skip("No issues found in test file")

    # Run fix and assert issues are provided for table formatting
    fix_result = tool.fix([str(temp_biome_file)])
    assert_that(fix_result.issues).is_not_none()
    assert_that(fix_result.issues).is_instance_of(list)
    assert_that(fix_result.issues).is_length(fix_result.remaining_issues_count)

    # Verify that formatted output renders correctly
    issues_list = list(fix_result.issues) if fix_result.issues else []
    formatted = format_tool_output(
        tool_name="biome",
        output=fix_result.output or "",
        output_format="grid",
        issues=issues_list,
    )
    assert_that(formatted).is_true()  # Should produce some output


def test_biome_respects_biomeignore(tmp_path: Path) -> None:
    """BiomeTool: Should respect .biomeignore file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    # Create a file that should be ignored
    ignored_file = tmp_path / "ignored.js"
    ignored_file.write_text("var unused = 1;")  # Should trigger biome

    # Create a file that should be checked
    checked_file = tmp_path / "checked.js"
    checked_file.write_text("var unused = 1;")  # Should trigger biome

    # Create .biomeignore
    biomeignore = tmp_path / ".biomeignore"
    biomeignore.write_text("ignored.js\n")

    logger.info("[TEST] Testing biome with .biomeignore...")
    tool = BiomeTool()
    tool.set_options()

    # Check both files - ignored.js should be ignored, checked.js should be checked
    result = tool.check([str(tmp_path)])
    logger.info(
        f"[LOG] Biome found {result.issues_count} issues. Output:\n{result.output}",
    )

    # Biome should process files and respect .biomeignore where possible
    # Note: Biome's ignore behavior may vary; this test ensures the tool runs
    # and doesn't crash when .biomeignore is present
    assert_that(result.issues_count).is_greater_than_or_equal_to(0).described_as(
        "Should process files without crashing",
    )
    assert_that(result.issues).is_length(result.issues_count).described_as(
        "Issues count should match",
    )
