"""Integration tests for hadolint tool."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.tools.implementations.tool_hadolint import HadolintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")
SAMPLE_FILE = "test_samples/tools/config/docker/Dockerfile.violations"


def run_hadolint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run hadolint directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with hadolint.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    import shutil
    import subprocess

    hadolint_path = shutil.which("hadolint")
    print(f"[DEBUG] hadolint binary path: {hadolint_path}")
    version_result = subprocess.run(
        ["hadolint", "--version"],
        capture_output=True,
        text=True,
    )
    print(f"[DEBUG] hadolint version: {version_result.stdout}")
    cmd = ["hadolint", "--no-color", "-f", "tty", str(file_path)]
    print(f"[DEBUG] Running hadolint command: {' '.join(cmd)}")
    with open(file_path) as f:
        print(f"[DEBUG] File contents for {file_path}:")
        print(f.read())
    with tempfile.TemporaryDirectory() as temp_home:
        env = os.environ.copy()
        env["HOME"] = temp_home
        print(
            f"[DEBUG] Subprocess environment: HOME={env.get('HOME')}, "
            f"PATH={env.get('PATH')}",
        )
        print(f"[DEBUG] Subprocess CWD: {file_path.parent}")
        print(f"[DEBUG] Subprocess full env: {env}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=file_path.parent,
            env=env,
        )
    issues = []
    for line in result.stdout.splitlines():
        if any(level in line for level in ["error:", "warning:", "info:", "style:"]):
            issues.append(line)
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return (success, result.stdout, issues_count)


@pytest.mark.hadolint
def test_hadolint_available() -> None:
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
def test_hadolint_reports_violations_direct(tmp_path) -> None:
    """Hadolint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()
    import os
    import shutil
    from pathlib import Path

    sample_file = tmp_path / "Dockerfile"
    shutil.copy(Path(SAMPLE_FILE), sample_file)
    print(f"[DEBUG] CWD: {os.getcwd()}")
    print(f"[DEBUG] Temp dir contents: {os.listdir(tmp_path)}")
    print(
        f"[DEBUG] Environment: HOME={os.environ.get('HOME')}, "
        f"PATH={os.environ.get('PATH')}",
    )
    logger.info("[TEST] Running hadolint directly on sample file...")
    success, output, issues = run_hadolint_directly(sample_file)
    logger.info(f"[LOG] Hadolint found {issues} issues. Output:\n{output}")
    assert_that(success).is_false().described_as(
        "Hadolint should fail when violations are present.",
    )
    assert_that(issues).is_greater_than(0).described_as(
        "Hadolint should report at least one issue.",
    )
    assert_that(any(code in output for code in ["DL", "SC"])).is_true().described_as(
        "Hadolint output should contain error codes.",
    )


@pytest.mark.hadolint
def test_hadolint_reports_violations_through_lintro(tmp_path) -> None:
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
        f"[LOG] Lintro HadolintTool found {result.issues_count} issues. "
        f"Output:\n{result.output}",
    )
    assert_that(result.success).is_false().described_as(
        "Lintro HadolintTool should fail when violations are present.",
    )
    assert_that(result.issues_count).is_greater_than(0).described_as(
        "Lintro HadolintTool should report at least one issue.",
    )
    assert_that(
        any(code in result.output for code in ["DL", "SC"]),
    ).is_true().described_as(
        "Lintro HadolintTool output should contain error codes.",
    )


@pytest.mark.hadolint
def test_hadolint_output_consistency_direct_vs_lintro(tmp_path) -> None:
    """Hadolint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()
    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    import os

    print(f"[DEBUG] CWD: {os.getcwd()}")
    print(f"[DEBUG] Temp dir contents: {os.listdir(tmp_path)}")
    print(
        f"[DEBUG] Environment: HOME={os.environ.get('HOME')}, "
        f"PATH={os.environ.get('PATH')}",
    )
    logger.info("[TEST] Comparing hadolint CLI and Lintro HadolintTool outputs...")
    tool = HadolintTool()
    tool.set_options(no_color=True, format="tty")
    direct_success, direct_output, direct_issues = run_hadolint_directly(sample_file)
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}",
    )
    assert_that(direct_issues).is_equal_to(result.issues_count), (
        f"Mismatch: CLI={direct_issues}, Lintro={result.issues_count}\n"
        f"CLI Output:\n{direct_output}\n"
        f"Lintro Output:\n{result.output}"
    )
    assert_that(direct_success).is_equal_to(result.success).described_as(
        "Success/failure mismatch between CLI and Lintro.",
    )
    assert_that(direct_issues).is_equal_to(result.issues_count).described_as(
        "Issue count mismatch between CLI and Lintro.",
    )


@pytest.mark.hadolint
def test_hadolint_with_ignore_rules(tmp_path) -> None:
    """Lintro HadolintTool: Should properly ignore specified rules.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()
    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing hadolint with ignore rules...")
    tool = HadolintTool()
    tool.set_options(no_color=True, format="tty")
    result_all = tool.check([str(sample_file)])
    tool_ignore = HadolintTool()
    tool_ignore.set_options(no_color=True, format="tty", ignore=["DL3007", "DL3003"])
    result_ignore = tool_ignore.check([str(sample_file)])
    logger.info(f"[LOG] Without ignore: {result_all.issues_count} issues")
    logger.info(f"[LOG] With ignore: {result_ignore.issues_count} issues")
    assert_that(result_ignore.issues_count <= result_all.issues_count).is_true()


@pytest.mark.hadolint
def test_hadolint_fix_method_not_implemented(tmp_path) -> None:
    """Lintro HadolintTool: .fix() should raise NotImplementedError.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()
    sample_file = tmp_path / "Dockerfile"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info(
        "[TEST] Verifying that HadolintTool.fix() raises NotImplementedError...",
    )
    tool = HadolintTool()
    with pytest.raises(NotImplementedError):
        tool.fix([str(sample_file)])
    logger.info("[LOG] NotImplementedError correctly raised by HadolintTool.fix().")


@pytest.mark.hadolint
def test_hadolint_empty_directory(tmp_path) -> None:
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
    assert_that(result.success).is_true().described_as(
        "Empty directory should be handled successfully.",
    )
    assert_that(result.issues_count).is_equal_to(
        0,
    ), "Empty directory should have no issues."


@pytest.mark.hadolint
def test_hadolint_parser_validation(tmp_path) -> None:
    """Test that hadolint parser correctly parses output.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_hadolint_available()
    from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output

    sample_output = (
        "Dockerfile:1 DL3006 error: Always tag the version of an image "
        "explicitly\n"
        "Dockerfile:4 DL3009 warning: Delete the apt-get lists after "
        "installing something\n"
        "Dockerfile:6 DL3015 info: Avoid additional packages by "
        "specifying `--no-install-recommends`"
    )
    issues = parse_hadolint_output(sample_output)
    logger.info(f"[LOG] Parsed {len(issues)} issues from sample output")
    assert_that(issues).is_length(3), "Should parse 3 issues"
    assert_that(issues[0].level).is_equal_to("error").described_as(
        "First issue should be error level",
    )
    assert_that(issues[0].code).is_equal_to("DL3006").described_as(
        "First issue should be DL3006",
    )
    assert_that(issues[1].level).is_equal_to("warning").described_as(
        "Second issue should be warning level",
    )
    assert_that(issues[2].level).is_equal_to("info").described_as(
        "Third issue should be info level",
    )
