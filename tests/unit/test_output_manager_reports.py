from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.output_manager import OutputManager


class DummyIssue:
    def __init__(self, file: str, line: int, code: str, message: str):
        self.file = file
        self.line = line
        self.code = code
        self.message = message


class DummyResult:
    def __init__(
        self, name: str, issues_count: int, issues: list[DummyIssue] | None = None
    ):
        self.name = name
        self.issues_count = issues_count
        self.issues = issues or []


def test_output_manager_writes_reports(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LINTRO_LOG_DIR", str(tmp_path))
    om = OutputManager()
    issues = [DummyIssue(file="a.py", line=1, code="X", message="m")]
    results = [DummyResult(name="ruff", issues_count=1, issues=issues)]
    om.write_reports_from_results(results=results)
    assert_that((om.run_dir / "report.md").exists()).is_true()
    assert_that((om.run_dir / "report.html").exists()).is_true()
    assert_that((om.run_dir / "summary.csv").exists()).is_true()
