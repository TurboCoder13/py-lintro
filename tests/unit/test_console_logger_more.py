from __future__ import annotations

from pathlib import Path

from lintro.utils.console_logger import create_logger


def test_console_logger_parsing_messages(tmp_path: Path, capsys):
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
    # Presence of tip about auto-fixable is enough to cover branch
    assert "auto-fixed" in out or "Would reformat" in out or "Found" in out
