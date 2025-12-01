"""Additional tests for console_logger small branches."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.console_logger import create_logger, get_tool_emoji


def test_get_tool_emoji_default() -> None:
    """Return a default emoji for unknown tools and non-empty string."""
    # Unknown tool should return the default emoji
    emoji = get_tool_emoji("unknown-tool")
    assert_that(emoji).is_not_empty()
    # Known tools return specific emojis, default is different character set
    assert_that(emoji).is_not_equal_to("")


def test_console_logger_parsing_messages(tmp_path: Path, capsys) -> None:
    """Parse typical messages and print a concise summary.

    Args:
        tmp_path: Temporary directory for artifacts.
        capsys: Pytest capture fixture.
    """
    logger = create_logger(run_dir=tmp_path, verbose=False, raw_output=False)
    raw = (
        "Fixed 1 issue(s)\n"
        "Found 2 issue(s) that cannot be auto-fixed\n"
        "Would reformat: a.py"
    )
    logger.print_tool_result(
        tool_name="ruff",
        output="formatted table",
        issues_count=2,
        raw_output_for_meta=raw,
        action="check",
    )
    out = capsys.readouterr().out
    assert_that(
        "auto-fixed" in out or "Would reformat" in out or "Found" in out,
    ).is_true()


def test_get_tool_emoji_pytest() -> None:
    """Test that pytest tool has the test emoji."""
    emoji_pt = get_tool_emoji("pt")
    emoji_pytest = get_tool_emoji("pytest")
    # Both should return test emoji
    assert_that(emoji_pt).is_not_empty()
    assert_that(emoji_pytest).is_not_empty()
    # Both should be the same emoji
    assert_that(emoji_pt).is_equal_to(emoji_pytest)
    # Should be the test emoji
    assert_that(emoji_pt).is_equal_to("🧪")


def test_console_logger_pytest_result_no_issues(
    tmp_path: Path,
    capsys,
) -> None:
    """Test print_tool_result for pytest with no issues.

    Args:
        tmp_path: Temporary directory for artifacts.
        capsys: Pytest capture fixture.
    """
    logger = create_logger(run_dir=tmp_path, verbose=False, raw_output=False)
    logger.print_tool_result(
        tool_name="pytest",
        output="All tests passed",
        issues_count=0,
        action="test",
        success=True,
    )
    out = capsys.readouterr().out
    # Should display test results section
    assert_that(out).contains("Test Results")


def test_console_logger_pytest_result_with_failures(
    tmp_path: Path,
    capsys,
) -> None:
    """Test print_tool_result for pytest with failures.

    Args:
        tmp_path: Temporary directory for artifacts.
        capsys: Pytest capture fixture.
    """
    logger = create_logger(run_dir=tmp_path, verbose=False, raw_output=False)
    logger.print_tool_result(
        tool_name="pt",
        output="2 tests failed",
        issues_count=2,
        action="test",
        success=False,
    )
    out = capsys.readouterr().out
    # Should display test results
    assert_that(out).contains("Test Results")


def test_console_logger_pytest_success_message(
    tmp_path: Path,
    capsys,
) -> None:
    """Test success message for pytest results.

    Args:
        tmp_path: Temporary directory for artifacts.
        capsys: Pytest capture fixture.
    """
    logger = create_logger(run_dir=tmp_path, verbose=False, raw_output=False)
    logger.success(message="All tests passed!")
    out = capsys.readouterr().out
    assert_that(out).contains("All tests passed!")


def test_console_logger_print_tool_header_pytest(
    tmp_path: Path,
    capsys,
) -> None:
    """Test print_tool_header for pytest.

    Args:
        tmp_path: Temporary directory for artifacts.
        capsys: Pytest capture fixture.
    """
    logger = create_logger(run_dir=tmp_path, verbose=False, raw_output=False)
    logger.print_tool_header(tool_name="pytest", action="test")
    out = capsys.readouterr().out
    # Should include the pytest tool name and action
    assert_that(out).contains("pytest")
    assert_that(out).contains("test")
