"""Extra tests for `BlackTool` to cover validations and no-files paths."""

from __future__ import annotations

from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.tools.implementations.tool_black import BlackTool


def test_black_set_options_validation_errors() -> None:
    """Validate type checking for option setters raises ValueError."""
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


def test_black_no_files_paths(tmp_path: Path, monkeypatch) -> None:
    """Return success and informative output when no files are discovered.

    Args:
        tmp_path: Temporary directory for file discovery.
        monkeypatch: Pytest patching of file discovery.
    """
    tool = BlackTool()
    # Stub discovery to empty list to simulate "no files to check/format"
    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [],
        raising=True,
    )

    res_check = tool.check([str(tmp_path)])
    assert_that(res_check.success).is_true()
    assert_that(res_check.issues_count).is_equal_to(0)
    assert_that(res_check.output or "").contains("No files")

    res_fix = tool.fix([str(tmp_path)])
    assert_that(res_fix.success).is_true()
    assert_that(res_fix.issues_count).is_equal_to(0)
    assert_that(res_fix.output or "").contains("No files")
