"""Additional tests for console_logger small branches."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.console_logger import create_logger, get_tool_emoji


def test_get_tool_emoji_default():
    """Return a default emoji for unknown tools and non-empty string."""
    # Unknown tool should return the default emoji
    emoji = get_tool_emoji("unknown-tool")
    assert_that(emoji).is_not_empty()
    # Known tools return specific emojis, default is different character set
    assert_that(emoji).is_not_equal_to("")


def test_console_logger_parsing_messages(tmp_path: Path, capsys):
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
