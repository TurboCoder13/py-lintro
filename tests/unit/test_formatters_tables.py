from __future__ import annotations

from assertpy import assert_that

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
    assert_that(desc.get_columns()).is_equal_to(["File", "Line", "Code", "Message"])
    rows = desc.get_rows(issues)
    assert_that(rows and len(rows[0]) == 4).is_true()
    out = format_darglint_issues(issues=issues, format="grid")
    assert_that(out).contains("D100")


def test_prettier_table_and_formatting(tmp_path):
    issues = [
        PrettierIssue(
            file=str(tmp_path / "f.js"),
            line=None,
            column=None,
            code="FORMAT",
            message="m",
        )
    ]
    desc = PrettierTableDescriptor()
    assert_that(desc.get_columns()).is_equal_to(
        ["File", "Line", "Column", "Code", "Message"]
    )
    rows = desc.get_rows(issues)
    assert_that(rows and len(rows[0]) == 5).is_true()
    out = format_prettier_issues(issues=issues, format="plain")
    assert_that("Auto-fixable" in out or out).is_true()


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
    assert_that(desc.get_columns()).is_equal_to(
        ["File", "Line", "Column", "Code", "Message"]
    )
    rows = desc.get_rows(issues)
    assert_that(rows and len(rows[0]) == 5).is_true()
    out = format_ruff_issues(issues=issues, format="grid")
    assert_that("Auto-fixable" in out or "Not auto-fixable" in out or out).is_true()


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
    assert_that(desc.get_columns()).is_equal_to(
        ["File", "Line", "Column", "Level", "Code", "Message"]
    )
    rows = desc.get_rows(issues)
    assert_that(rows and len(rows[0]) == 6).is_true()
    out = format_hadolint_issues(issues=issues, format="markdown")
    assert_that(out).contains("DL3001")
