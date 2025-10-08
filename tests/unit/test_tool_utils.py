"""Unit tests for tool_utils helpers and tabulate formatting."""

from __future__ import annotations

from assertpy import assert_that

from lintro.utils.tool_utils import (
    _is_venv_directory,
    format_as_table,
    should_exclude_path,
    walk_files_with_excludes,
)


def test_should_exclude_path_patterns():
    """Evaluate exclude pattern behavior on file paths."""
    assert_that(should_exclude_path("a/b/.venv/lib.py", [".venv"]) is True).is_true()
    assert_that(should_exclude_path("a/b/c.py", ["*.md"]) is False).is_true()
    assert_that(should_exclude_path("dir/file.md", ["*.md"]) is True).is_true()


def test_get_table_columns_and_format_tabulate(monkeypatch):
    """Use tabulate when available and validate headers/rows are passed.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub tabulate.
    """
    rows_captured = {}

    def fake_tabulate(
        tabular_data,
        headers,
        tablefmt,
        stralign=None,
        disable_numparse=None,
    ):
        rows_captured["headers"] = headers
        rows_captured["rows"] = tabular_data
        return "TABLE"

    monkeypatch.setitem(
        __import__("lintro.utils.tool_utils").utils.tool_utils.__dict__,
        "tabulate",
        fake_tabulate,
    )
    monkeypatch.setitem(
        __import__("lintro.utils.tool_utils").utils.tool_utils.__dict__,
        "TABULATE_AVAILABLE",
        True,
    )
    issues = [
        {"file": "a.py", "line": 1, "column": 2, "code": "X", "message": "m"},
        {"file": "b.py", "line": 3, "column": 4, "code": "Y", "message": "n"},
    ]
    table = format_as_table(issues=issues, tool_name="unknown", group_by=None)
    assert_that(table).is_equal_to("TABLE")
    assert_that(rows_captured["headers"]).is_true()
    assert_that(rows_captured["rows"]).is_true()


def test_walk_files_with_excludes(tmp_path):
    """Walk files with include/exclude patterns.

    Args:
        tmp_path: Temporary directory fixture to build a sample tree.
    """
    d = tmp_path / "proj"
    (d / "sub").mkdir(parents=True)
    (d / "sub" / "a.py").write_text("x")
    (d / "sub" / "b.js").write_text("x")
    (d / "sub" / "ignore.txt").write_text("x")
    files = walk_files_with_excludes(
        paths=[str(d)],
        file_patterns=["*.py", "*.js"],
        exclude_patterns=["ignore*"],
        include_venv=False,
    )
    assert_that(any(p.endswith("a.py") for p in files)).is_true()
    assert_that(any(p.endswith("b.js") for p in files)).is_true()
    assert_that(any(p.endswith("ignore.txt") for p in files)).is_false()


def test_is_venv_directory_predicate():
    """Detect typical virtual environment directory names."""
    assert_that(_is_venv_directory(".venv")).is_true()
    assert_that(_is_venv_directory("venv")).is_true()
    assert_that(_is_venv_directory("site-packages")).is_true()
    assert_that(_is_venv_directory("src")).is_false()
