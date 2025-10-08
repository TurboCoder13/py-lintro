"""Unit tests for BanditTool command building and config hydration."""

from assertpy import assert_that

from lintro.tools.implementations.tool_bandit import BanditTool


def test_build_check_command_basic() -> None:
    """Build a basic bandit check command and verify core flags are set."""
    tool = BanditTool()
    cmd = tool._build_check_command(["a.py"])
    assert_that(cmd[0:3]).contains("bandit")
    assert_that(cmd).contains("-r")
    assert_that("-f" in cmd and "json" in cmd).is_true()
    assert_that(cmd.count("-q")).is_equal_to(1)
    assert_that(cmd).contains("a.py")


def test_build_check_command_with_severity_confidence() -> None:
    """Include severity and confidence options in the bandit command."""
    tool = BanditTool()
    tool.set_options(severity="HIGH", confidence="MEDIUM")
    cmd = tool._build_check_command(["a.py"])
    assert_that(cmd).contains("-lll")
    assert_that(cmd).contains("-ii")


def test_build_check_command_with_various_options() -> None:
    """Include a wide range of options in the constructed bandit command."""
    tool = BanditTool()
    tool.set_options(
        tests="B101,B102",
        skips="B201",
        profile="secure",
        configfile="bandit.toml",
        baseline="baseline.json",
        ignore_nosec=True,
        aggregate="file",
        verbose=True,
        quiet=True,
    )
    cmd = tool._build_check_command(["a.py"])
    assert_that("-t" in cmd and "B101,B102" in cmd).is_true()
    assert_that("-s" in cmd and "B201" in cmd).is_true()
    assert_that("-p" in cmd and "secure" in cmd).is_true()
    assert_that("-c" in cmd and "bandit.toml" in cmd).is_true()
    assert_that("-b" in cmd and "baseline.json" in cmd).is_true()
    assert_that(cmd).contains("--ignore-nosec")
    assert_that("-a" in cmd and "file" in cmd).is_true()
    assert_that(cmd).contains("-v")
    assert_that(cmd.count("-q")).is_equal_to(1)
