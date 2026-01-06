"""Integration tests for yamllint tool."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.enums.severity_level import SeverityLevel
from lintro.tools.implementations.yamllint_config import YamllintTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")
SAMPLE_FILE = "test_samples/tools/config/yaml/yaml_violations.yml"


def run_yamllint_directly(file_path: Path) -> tuple[bool, str, int]:
    """Run yamllint directly on a file and return result tuple.

    Args:
        file_path: Path to the file to check with yamllint.

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    import shutil
    import subprocess

    yamllint_path = shutil.which("yamllint")
    print(f"[DEBUG] yamllint binary path: {yamllint_path}")
    version_result = subprocess.run(
        ["yamllint", "--version"],
        capture_output=True,
        text=True,
    )
    print(f"[DEBUG] yamllint version: {version_result.stdout}")
    cmd = ["yamllint", "-f", "parsable", file_path.name]
    print(f"[DEBUG] Running yamllint command: {' '.join(cmd)}")
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
        if any(level in line for level in ["[error]", "[warning]"]):
            issues.append(line)
    issues_count = len(issues)
    success = issues_count == 0 and result.returncode == 0
    return (success, result.stdout, issues_count)


@pytest.mark.yamllint
def test_yamllint_available() -> None:
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
def test_yamllint_reports_violations_direct(tmp_path: Path) -> None:
    """Yamllint CLI: Should detect and report violations in a sample file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    import os
    import shutil

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    config_dst = tmp_path / ".yamllint"
    config_dst.write_text("extends: default\n")
    print(f"[DEBUG] CWD: {os.getcwd()}")
    print(f"[DEBUG] Temp dir contents: {os.listdir(tmp_path)}")
    print(
        f"[DEBUG] Environment: HOME={os.environ.get('HOME')}, "
        f"PATH={os.environ.get('PATH')}",
    )
    logger.info("[TEST] Running yamllint directly on sample file...")
    success, output, issues = run_yamllint_directly(sample_file)
    logger.info(f"[LOG] Yamllint found {issues} issues. Output:\n{output}")
    assert_that(success).is_false().described_as(
        "Yamllint should fail when violations are present.",
    )
    assert_that(issues).is_greater_than(0).described_as(
        "Yamllint should report at least one issue.",
    )
    assert_that(
        any(level in output for level in ["[error]", "[warning]"]),
    ).is_true().described_as("Yamllint output should contain issue levels.")


@pytest.mark.yamllint
def test_yamllint_reports_violations_through_lintro(tmp_path: Path) -> None:
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
        f"[LOG] Lintro YamllintTool found {result.issues_count} issues. "
        f"Output:\n{result.output}",
    )
    assert_that(result.success).is_false().described_as(
        "Lintro YamllintTool should fail when violations are present.",
    )
    assert_that(result.issues_count).is_greater_than(0).described_as(
        "Lintro YamllintTool should report at least one issue.",
    )
    assert_that(result.issues).is_not_empty().described_as(
        "Parsed issues list should be present",
    )
    assert_that(result.issues).is_not_none()
    issues = result.issues
    if issues is None:
        pytest.fail("issues should not be None")
    assert_that(
        any(
            getattr(i, "level", None) in {SeverityLevel.ERROR, SeverityLevel.WARNING}
            for i in issues
        ),
    ).is_true().described_as("Parsed issues should include error or warning levels.")


@pytest.mark.yamllint
def test_yamllint_output_consistency_direct_vs_lintro(tmp_path: Path) -> None:
    """Yamllint CLI vs Lintro: Should produce consistent results for the same file.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    import os
    import shutil

    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    config_dst = tmp_path / ".yamllint"
    config_dst.write_text("extends: default\n")
    print(f"[DEBUG] CWD: {os.getcwd()}")
    print(f"[DEBUG] Temp dir contents: {os.listdir(tmp_path)}")
    print(
        f"[DEBUG] Environment: HOME={os.environ.get('HOME')}, "
        f"PATH={os.environ.get('PATH')}",
    )
    print(
        f"[DEBUG] Environment: HOME={os.environ.get('HOME')}, "
        f"PATH={os.environ.get('PATH')}",
    )
    logger.info("[TEST] Comparing yamllint CLI and Lintro YamllintTool outputs...")
    tool = YamllintTool()
    # Use config_data to ensure we use default config, not project's .yamllint
    tool.set_options(format="parsable", config_data="extends: default")
    direct_success, direct_output, direct_issues = run_yamllint_directly(sample_file)
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] CLI issues: {direct_issues}, Lintro issues: {result.issues_count}",
    )
    assert_that(direct_issues).is_equal_to(result.issues_count), (
        f"Mismatch: CLI={direct_issues}, Lintro={result.issues_count}\n"
        f"CLI Output:\n{direct_output}\n"
        f"Lintro Output:\n{result.output}"
    )


@pytest.mark.yamllint
def test_yamllint_with_config_options(tmp_path: Path) -> None:
    """Lintro YamllintTool: Should properly handle config options.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing yamllint with config options...")
    tool = YamllintTool()
    tool.set_options(format="parsable")
    result_default = tool.check([str(sample_file)])
    tool_relaxed = YamllintTool()
    tool_relaxed.set_options(format="parsable", relaxed=True)
    result_relaxed = tool_relaxed.check([str(sample_file)])
    logger.info(f"[LOG] Default config: {result_default.issues_count} issues")
    logger.info(f"[LOG] Relaxed config: {result_relaxed.issues_count} issues")
    assert_that(result_relaxed.issues_count <= result_default.issues_count).is_true()


@pytest.mark.yamllint
def test_yamllint_with_no_warnings_option(tmp_path: Path) -> None:
    """Lintro YamllintTool: Should properly handle no-warnings option.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    sample_file = tmp_path / "test.yml"
    shutil.copy(SAMPLE_FILE, sample_file)
    logger.info("[TEST] Testing yamllint with no-warnings option...")
    tool = YamllintTool()
    tool.set_options(format="parsable")
    result_all = tool.check([str(sample_file)])
    tool_no_warnings = YamllintTool()
    tool_no_warnings.set_options(format="parsable", no_warnings=True)
    result_no_warnings = tool_no_warnings.check([str(sample_file)])
    logger.info(f"[LOG] All issues: {result_all.issues_count} issues")
    logger.info(f"[LOG] No warnings: {result_no_warnings.issues_count} issues")
    assert_that(result_no_warnings.issues_count <= result_all.issues_count).is_true()


@pytest.mark.yamllint
def test_yamllint_fix_method_implemented(tmp_path: Path) -> None:
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
    assert_that(result.success).is_instance_of(bool).described_as(
        "Fix should return a boolean success value",
    )
    assert_that(result.issues_count).is_instance_of(int).described_as(
        "Fix should return an integer issue count",
    )


@pytest.mark.yamllint
def test_yamllint_empty_directory(tmp_path: Path) -> None:
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
    assert_that(result.success).is_true().described_as(
        "Empty directory should be handled successfully.",
    )
    assert_that(result.issues_count).is_equal_to(
        0,
    ), "Empty directory should have no issues."


@pytest.mark.yamllint
def test_yamllint_parser_validation(tmp_path: Path) -> None:
    """Test that yamllint parser correctly parses output.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output

    sample_output = (
        "file.yaml:1:1: [error] too many blank lines (1 > 0 allowed) "
        "(empty-lines)\n"
        "file.yaml:3:5: [warning] wrong indentation: expected 4 but found 2 "
        "(indentation)\n"
        "file.yaml:7:80: [error] line too long (120 > 79 characters) "
        "(line-length)"
    )
    issues = parse_yamllint_output(sample_output)
    logger.info(f"[LOG] Parsed {len(issues)} issues from sample output")
    assert_that(issues).described_as("Should parse 3 issues").is_length(3)
    from lintro.enums.severity_level import SeverityLevel

    assert_that(issues[0].level).is_equal_to(SeverityLevel.ERROR).described_as(
        "First issue should be error level",
    )
    assert_that(issues[0].rule).is_equal_to("empty-lines").described_as(
        "First issue should be empty-lines rule",
    )
    assert_that(issues[1].level).is_equal_to(SeverityLevel.WARNING).described_as(
        "Second issue should be warning level",
    )
    assert_that(issues[1].rule).is_equal_to("indentation").described_as(
        "Second issue should be indentation rule",
    )
    assert_that(issues[2].level).is_equal_to(SeverityLevel.ERROR).described_as(
        "Third issue should be error level",
    )
    assert_that(issues[2].rule).is_equal_to("line-length").described_as(
        "Third issue should be line-length rule",
    )


@pytest.mark.yamllint
def test_yamllint_config_discovery(tmp_path: Path) -> None:
    """YamllintTool: Should discover .yamllint config file correctly.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    test_yamllint_available()
    sample_file = tmp_path / "test.yml"
    sample_file.write_text("key: value\n")  # Valid YAML

    # Create .yamllint config that disables document-start rule
    yamllint_config = tmp_path / ".yamllint"
    yamllint_config.write_text(
        "extends: default\nrules:\n  document-start: disable\n",
    )

    logger.info("[TEST] Testing yamllint config discovery...")
    tool = YamllintTool()
    tool.set_options(format="parsable")
    # Don't explicitly set config_file - should discover .yamllint automatically
    result = tool.check([str(sample_file)])
    logger.info(
        f"[LOG] Yamllint found {result.issues_count} issues with "
        f"auto-discovered config. Output:\n{result.output}",
    )
    # Should succeed with document-start rule disabled
    assert_that(result.success).is_true().described_as(
        "Should succeed with document-start rule disabled",
    )
    assert_that(result.issues_count).is_equal_to(0).described_as(
        "Should have no issues with document-start disabled",
    )
