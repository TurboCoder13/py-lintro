from __future__ import annotations

from pathlib import Path

import pytest

from lintro.utils.console_logger import SimpleLintroLogger, create_logger


def test_create_logger_and_basic_methods(tmp_path: Path, capsys: pytest.CaptureFixture):
    logger = create_logger(run_dir=tmp_path, verbose=True, raw_output=False)
    assert isinstance(logger, SimpleLintroLogger)

    # Basic logging paths
    logger.info("info message")
    logger.debug("debug message")
    logger.warning("warn message")
    logger.error("error message")

    # Headers
    logger.print_lintro_header(action="check", tool_count=1, tools_list="ruff")
    logger.print_tool_header(tool_name="ruff", action="check")

    # Tool result with no issues
    logger.print_tool_result(tool_name="ruff", output="", issues_count=0)

    # Tool result with issues and fixable hints in raw output
    raw = """
    [*] 2 fixable
    Formatting issues:
    Would reformat: file1.py
    Would reformat: file2.py
    Found 3 issue(s) that cannot be auto-fixed
    """.strip()
    logger.print_tool_result(
        tool_name="ruff",
        output="some formatted table",
        issues_count=3,
        raw_output_for_meta=raw,
        action="check",
    )

    # Execution summary: check
    class Result:
        def __init__(
            self, name: str, issues_count: int, success: bool, output: str = ""
        ):
            self.name = name
            self.issues_count = issues_count
            self.success = success
            self.output = output

    logger.print_execution_summary(
        action="check",
        tool_results=[Result("ruff", 1, False)],
    )

    # Execution summary: fmt with standardized counters
    class FmtResult:
        def __init__(
            self,
            name: str,
            fixed: int,
            remaining: int,
            success: bool = True,
            output: str = "",
        ):
            self.name = name
            self.fixed_issues_count = fixed
            self.remaining_issues_count = remaining
            self.success = success
            self.output = output

    logger.print_execution_summary(
        action="fmt",
        tool_results=[FmtResult("ruff", fixed=2, remaining=0, success=True)],
    )

    # Save console log
    logger.save_console_log()
    assert (tmp_path / "console.log").exists()

    out = capsys.readouterr().out
    # Spot-check a few outputs appeared
    assert "LINTRO" in out
    assert "Running ruff (check)" in out
    assert "Auto-fixable" in out or "No issues found" in out
