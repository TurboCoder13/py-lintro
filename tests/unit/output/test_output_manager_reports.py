"""Unit tests for report generation via OutputManager."""

from __future__ import annotations

from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.utils.output_manager import OutputManager


class DummyIssue:
    """Simple container for issue fields used in reports."""

    def __init__(self, file: str, line: int, code: str, message: str) -> None:
        """Initialize an issue container.

        Args:
            file: File path where the issue occurred.
            line: Line number of the issue.
            code: Issue code identifier.
            message: Human-readable message.
        """
        self.file = file
        self.line = line
        self.code = code
        self.message = message


class DummyResult:
    """Simple result container used to exercise report writing."""

    def __init__(
        self,
        name: str,
        issues_count: int,
        issues: list[DummyIssue] | None = None,
    ) -> None:
        """Initialize a result wrapper.

        Args:
            name: Tool name associated with the result.
            issues_count: Total number of issues.
            issues: Optional list of issue objects.
        """
        self.name = name
        self.issues_count = issues_count
        self.issues = issues or []


def test_output_manager_writes_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Write multiple report formats and verify artifacts exist.

    Args:
        tmp_path: Temporary directory for placing report outputs.
        monkeypatch: Pytest monkeypatch to set output directory.
    """
    monkeypatch.setenv("LINTRO_LOG_DIR", str(tmp_path))
    om = OutputManager()
    issues = [DummyIssue(file="a.py", line=1, code="X", message="m")]
    results = [DummyResult(name="ruff", issues_count=1, issues=issues)]
    om.write_reports_from_results(results=results)  # type: ignore[arg-type]
    assert_that((om.run_dir / "report.md").exists()).is_true()
    assert_that((om.run_dir / "report.html").exists()).is_true()
    assert_that((om.run_dir / "summary.csv").exists()).is_true()
