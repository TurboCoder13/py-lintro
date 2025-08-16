from __future__ import annotations

from lintro.formatters.tools.darglint_formatter import (
    DarglintTableDescriptor,
    format_darglint_issues,
)
from lintro.formatters.tools.hadolint_formatter import (
    HadolintTableDescriptor,
    format_hadolint_issues,
)
from lintro.formatters.tools.prettier_formatter import (
    PrettierTableDescriptor,
    format_prettier_issues,
)
from lintro.formatters.tools.ruff_formatter import (
    RuffTableDescriptor,
    format_ruff_issues,
)
from lintro.parsers.darglint.darglint_issue import DarglintIssue
from lintro.parsers.hadolint.hadolint_issue import HadolintIssue
from lintro.parsers.prettier.prettier_issue import PrettierIssue
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue


def test_darglint_table_and_formatting(tmp_path):
    issues = [
        DarglintIssue(file=str(tmp_path / "f.py"), line=1, code="D100", message="m")
    ]
    desc = DarglintTableDescriptor()
    assert desc.get_columns() == ["File", "Line", "Code", "Message"]
    rows = desc.get_rows(issues)
    assert rows and len(rows[0]) == 4
    out = format_darglint_issues(issues=issues, format="grid")
    assert "D100" in out


def test_prettier_table_and_formatting(tmp_path):
    issues = [
        PrettierIssue(
            file=str(tmp_path / "f.js"),
            line=None,
            column=None,
            code="FORMAT",
            message="m",
        ),
    ]
    desc = PrettierTableDescriptor()
    assert desc.get_columns() == ["File", "Line", "Column", "Code", "Message"]
    rows = desc.get_rows(issues)
    assert rows and len(rows[0]) == 5
    out = format_prettier_issues(issues=issues, format="plain")
    assert "Auto-fixable" in out or out


def test_ruff_table_and_formatting(tmp_path):
    issues = [
        RuffIssue(
            file=str(tmp_path / "f.py"),
            line=1,
            column=2,
            code="E123",
            message="m",
            fixable=False,
        ),
        RuffFormatIssue(file=str(tmp_path / "g.py")),
    ]
    desc = RuffTableDescriptor()
    assert desc.get_columns() == ["File", "Line", "Column", "Code", "Message"]
    rows = desc.get_rows(issues)
    assert rows and len(rows[0]) == 5
    out = format_ruff_issues(issues=issues, format="grid")
    assert "Auto-fixable" in out or "Not auto-fixable" in out or out


def test_hadolint_table_and_formatting(tmp_path):
    issues = [
        HadolintIssue(
            file=str(tmp_path / "Dockerfile"),
            line=1,
            column=1,
            level="error",
            code="DL3001",
            message="Test",
        )
    ]
    desc = HadolintTableDescriptor()
    assert desc.get_columns() == ["File", "Line", "Column", "Level", "Code", "Message"]
    rows = desc.get_rows(issues)
    assert rows and len(rows[0]) == 6
    out = format_hadolint_issues(issues=issues, format="markdown")
    assert "DL3001" in out
