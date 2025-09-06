"""Extra tests for `BlackTool` to cover validations and no-files paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from lintro.tools.implementations.tool_black import BlackTool


def test_black_set_options_validation_errors():
    tool = BlackTool()
    with pytest.raises(ValueError):
        tool.set_options(line_length="88")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tool.set_options(target_version=123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tool.set_options(fast="yes")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tool.set_options(preview="no")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tool.set_options(diff="maybe")  # type: ignore[arg-type]


def test_black_no_files_paths(tmp_path: Path, monkeypatch):
    tool = BlackTool()
    # Stub discovery to empty list to simulate "no files to check/format"
    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [],
        raising=True,
    )

    res_check = tool.check([str(tmp_path)])
    assert res_check.success and res_check.issues_count == 0
    assert "No files" in (res_check.output or "")

    res_fix = tool.fix([str(tmp_path)])
    assert res_fix.success and res_fix.issues_count == 0
    assert "No files" in (res_fix.output or "")
