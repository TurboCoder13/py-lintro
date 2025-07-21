"""Integration tests for yamllint tool."""

import subprocess
from pathlib import Path
import shutil

import pytest
from loguru import logger

from lintro.tools.implementations.tool_yamllint import YamllintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = "test_samples/yaml_violations.yml"


def run_yamllint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run yamllint directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with yamllint.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    cmd = [
        "yamllint",
        "--format",
        "parsable",
        file_path.name,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=file_path.parent,
    )
    # Count issues by parsing output lines that contain error/warning patterns
    issues = []
    for line in result.stdout.splitlines():
        if any(level in line for level in ["[error]", "[warning]"]):
            issues.append(line)
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return success, result.stdout, issues_count


@pytest.mark.yamllint
def test_yamllint_available():
    """Check if yamllint is available in PATH."""
    try:
        result = subprocess.run(
            ["yamllint", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("yamllint not available")
    except FileNotFoundError:
        pytest.skip("yamllint not available")


@pytest.mark.yamllint
def test_yamllint_reports_violations_direct(tmp_path):
    """Yamllint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Running yamllint directly on sample file...")
    success, output, issues = run_yamllint_directly(sample_file)
    logger.info(f"[LOG] Yamllint found {issues} issues. Output:\n{output}")
    assert not success, "Yamllint should fail when violations are present."
    assert issues > 0, "Yamllint should report at least one issue."
    assert any(level in output for level in ["[error]", "[warning]"]), (
        "Yamllint output should contain issue levels."
    )


@pytest.mark.yamllint
def test_yamllint_reports_violations_through_lintro(tmp_path):
    """Lintro YamllintTool: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(f"SAMPLE_FILE: {sample_file}, exists: {sample_file.exists()}")
    logger.info("[TEST] Running YamllintTool through lintro on sample file...")
    tool = YamllintTool()
    tool.set_options(format="parsable")
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] Lintro YamllintTool found {result.issues_count} issues. Output:\n{result.output}"
    )
    assert not result.success, (
        "Lintro YamllintTool should fail when violations are present."
    )
    assert result.issues_count > 0, (
        "Lintro YamllintTool should report at least one issue."
    )
    assert any(level in result.output for level in ["[error]", "[warning]"]), (
        "Lintro YamllintTool output should contain issue levels."
    )


@pytest.mark.yamllint
def test_yamllint_output_consistency_direct_vs_lintro(tmp_path):
    """Yamllint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Comparing yamllint CLI and Lintro YamllintTool outputs...")
    tool = YamllintTool()
    tool.set_options(format="parsable")
    direct_success, direct_output, direct_issues = run_yamllint_directly(sample_file)
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


@pytest.mark.yamllint
def test_yamllint_with_config_options(tmp_path):
    """Lintro YamllintTool: Should properly handle config options.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing yamllint with config options...")

    # First run with default config
    tool = YamllintTool()
    tool.set_options(format="parsable")
    result_default = tool.check([str(sample_file)])

    # Then run with relaxed config (should have fewer issues)
    tool_relaxed = YamllintTool()
    tool_relaxed.set_options(format="parsable", relaxed=True)
    result_relaxed = tool_relaxed.check([str(sample_file)])

    logger.info(f"[LOG] Default config: {result_default.issues_count} issues")
    logger.info(f"[LOG] Relaxed config: {result_relaxed.issues_count} issues")

    # Relaxed config should have fewer or equal issues
    assert result_relaxed.issues_count <= result_default.issues_count


@pytest.mark.yamllint
def test_yamllint_with_no_warnings_option(tmp_path):
    """Lintro YamllintTool: Should properly handle no-warnings option.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing yamllint with no-warnings option...")

    # First run with all issues
    tool = YamllintTool()
    tool.set_options(format="parsable")
    result_all = tool.check([str(sample_file)])

    # Then run with no warnings (only errors)
    tool_no_warnings = YamllintTool()
    tool_no_warnings.set_options(format="parsable", no_warnings=True)
    result_no_warnings = tool_no_warnings.check([str(sample_file)])

    logger.info(f"[LOG] All issues: {result_all.issues_count} issues")
    logger.info(f"[LOG] No warnings: {result_no_warnings.issues_count} issues")

    # No warnings should have fewer or equal issues
    assert result_no_warnings.issues_count <= result_all.issues_count


@pytest.mark.yamllint
def test_yamllint_fix_method_implemented(tmp_path):
    """Lintro YamllintTool: .fix() should be implemented and work correctly.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Verifying that YamllintTool.fix() is implemented and works...")
    tool = YamllintTool()
    result = tool.fix([str(sample_file)])
    logger.info(f"[LOG] Fix result: {result.success}, {result.issues_count} issues")
    # The fix method should work without raising NotImplementedError
    assert isinstance(result.success, bool), "Fix should return a boolean success value"
    assert isinstance(result.issues_count, int), (
        "Fix should return an integer issue count"
    )


@pytest.mark.yamllint
def test_yamllint_empty_directory(tmp_path):
    """Lintro YamllintTool: Should handle empty directories gracefully.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    logger.info("[TEST] Testing yamllint with empty directory...")
    tool = YamllintTool()
    result = tool.check([str(empty_dir)])
    logger.info(f"[LOG] Empty directory result: {result.success}, {result.output}")
    assert result.success, "Empty directory should be handled successfully."
    assert result.issues_count == 0, "Empty directory should have no issues."


@pytest.mark.yamllint
def test_yamllint_parser_validation(tmp_path):
    """Test that yamllint parser correctly parses output.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()

    from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output

    # Test with sample output
    sample_output = """file.yaml:1:1: [error] too many blank lines (1 > 0 allowed) (empty-lines)
file.yaml:3:5: [warning] wrong indentation: expected 4 but found 2 (indentation)
file.yaml:7:80: [error] line too long (120 > 79 characters) (line-length)"""

    issues = parse_yamllint_output(sample_output)
    logger.info(f"[LOG] Parsed {len(issues)} issues from sample output")

    assert len(issues) == 3, "Should parse 3 issues"
    assert issues[0].level == "error", "First issue should be error level"
    assert issues[0].rule == "empty-lines", "First issue should be empty-lines rule"
    assert issues[1].level == "warning", "Second issue should be warning level"
    assert issues[1].rule == "indentation", "Second issue should be indentation rule"
    assert issues[2].level == "error", "Third issue should be error level"
    assert issues[2].rule == "line-length", "Third issue should be line-length rule"
