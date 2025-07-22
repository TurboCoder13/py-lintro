"""Integration tests for hadolint tool."""

import subprocess
from pathlib import Path
import shutil

import pytest
from loguru import logger

from lintro.tools.implementations.tool_hadolint import HadolintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_FILE = "test_samples/hadolint_violations"


def run_hadolint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run hadolint directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with hadolint.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    cmd = [
        "hadolint",
        "--no-color",
        "--format",
        "tty",
        file_path.name,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=file_path.parent,
    )
    # Count issues by parsing output lines that contain error/warning/info patterns
    issues = []
    for line in result.stdout.splitlines():
        if any(level in line for level in ["error:", "warning:", "info:", "style:"]):
            issues.append(line)
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return success, result.stdout, issues_count


@pytest.mark.hadolint
def test_hadolint_available():
    """Check if hadolint is available in PATH."""
    try:
        result = subprocess.run(
            ["hadolint", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("hadolint not available")
    except FileNotFoundError:
        pytest.skip("hadolint not available")


@pytest.mark.hadolint
def test_hadolint_reports_violations_direct(tmp_path):
    """Hadolint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Running hadolint directly on sample file...")
    success, output, issues = run_hadolint_directly(sample_file)
    logger.info(f"[LOG] Hadolint found {issues} issues. Output:\n{output}")
    assert not success, "Hadolint should fail when violations are present."
    assert issues > 0, "Hadolint should report at least one issue."
    assert any(code in output for code in ["DL", "SC"]), (
        "Hadolint output should contain error codes."
    )


@pytest.mark.hadolint
def test_hadolint_reports_violations_through_lintro(tmp_path):
    """Lintro HadolintTool: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(f"SAMPLE_FILE: {sample_file}, exists: {sample_file.exists()}")
    logger.info("[TEST] Running HadolintTool through lintro on sample file...")
    tool = HadolintTool()
    tool.set_options(no_color=True, format="tty")
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] Lintro HadolintTool found {result.issues_count} issues. Output:\n{result.output}"
    )
    assert not result.success, (
        "Lintro HadolintTool should fail when violations are present."
    )
    assert result.issues_count > 0, (
        "Lintro HadolintTool should report at least one issue."
    )
    assert any(code in result.output for code in ["DL", "SC"]), (
        "Lintro HadolintTool output should contain error codes."
    )


@pytest.mark.hadolint
def test_hadolint_output_consistency_direct_vs_lintro(tmp_path):
    """Hadolint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Comparing hadolint CLI and Lintro HadolintTool outputs...")
    tool = HadolintTool()
    tool.set_options(no_color=True, format="tty")
    direct_success, direct_output, direct_issues = run_hadolint_directly(sample_file)
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


@pytest.mark.hadolint
def test_hadolint_with_ignore_rules(tmp_path):
    """Lintro HadolintTool: Should properly ignore specified rules.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing hadolint with ignore rules...")

    # First run without ignoring rules
    tool = HadolintTool()
    tool.set_options(no_color=True, format="tty")
    result_all = tool.check([str(sample_file)])

    # Then run with some rules ignored
    tool_ignore = HadolintTool()
    tool_ignore.set_options(
        no_color=True,
        format="tty",
        ignore=[
            "DL3007",
            "DL3003",
        ],  # Ignore "using latest" and "use WORKDIR" violations
    )
    result_ignore = tool_ignore.check([str(sample_file)])

    logger.info(f"[LOG] Without ignore: {result_all.issues_count} issues")
    logger.info(f"[LOG] With ignore: {result_ignore.issues_count} issues")

    # Should have fewer or equal issues when ignoring rules
    assert result_ignore.issues_count <= result_all.issues_count


@pytest.mark.hadolint
def test_hadolint_fix_method_not_implemented(tmp_path):
    """Lintro HadolintTool: .fix() should raise NotImplementedError.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(
        "[TEST] Verifying that HadolintTool.fix() raises NotImplementedError..."
    )
    tool = HadolintTool()
    with pytest.raises(NotImplementedError):
        tool.fix([str(sample_file)])
    logger.info("[LOG] NotImplementedError correctly raised by HadolintTool.fix().")


@pytest.mark.hadolint
def test_hadolint_empty_directory(tmp_path):
    """Lintro HadolintTool: Should handle empty directories gracefully.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    logger.info("[TEST] Testing hadolint with empty directory...")
    tool = HadolintTool()
    result = tool.check([str(empty_dir)])
    logger.info(f"[LOG] Empty directory result: {result.success}, {result.output}")
    assert result.success, "Empty directory should be handled successfully."
    assert result.issues_count == 0, "Empty directory should have no issues."


@pytest.mark.hadolint
def test_hadolint_parser_validation(tmp_path):
    """Test that hadolint parser correctly parses output.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()

    from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output

    # Test with sample output
    sample_output = """Dockerfile:1 DL3006 error: Always tag the version of an image explicitly
Dockerfile:4 DL3009 warning: Delete the apt-get lists after installing something
Dockerfile:6 DL3015 info: Avoid additional packages by specifying `--no-install-recommends`"""

    issues = parse_hadolint_output(sample_output)
    logger.info(f"[LOG] Parsed {len(issues)} issues from sample output")

    assert len(issues) == 3, "Should parse 3 issues"
    assert issues[0].level == "error", "First issue should be error level"
    assert issues[0].code == "DL3006", "First issue should be DL3006"
    assert issues[1].level == "warning", "Second issue should be warning level"
    assert issues[2].level == "info", "Third issue should be info level"
