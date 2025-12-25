"""Integration tests for Bandit tool (security linter)."""

import contextlib
import os
import shutil
import tempfile

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_bandit import BanditTool


@pytest.mark.skipif(
    shutil.which("bandit") is None,
    reason="Bandit not installed on PATH; skip integration test.",
)
def test_bandit_detects_issues_on_sample_file() -> None:
    """Run BanditTool against a known vulnerable sample and expect findings."""
    tool = BanditTool()
    sample = os.path.abspath("test_samples/tools/python/bandit/bandit_violations.py")
    assert_that(os.path.exists(sample)).is_true()
    result: ToolResult = tool.check([sample])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("bandit")
    assert_that(result.issues_count > 0).is_true()
    logger.info(f"[TEST] bandit found {result.issues_count} issues on sample file")


@pytest.mark.skipif(
    shutil.which("bandit") is None,
    reason="Bandit not installed on PATH; skip integration test.",
)
def test_bandit_no_crash_on_clean_temp_file() -> None:
    """Bandit should handle a trivial (clean) temp file gracefully."""
    tool = BanditTool()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def ok():\n    return 0\n")
        f.flush()
        path = f.name
    try:
        result: ToolResult = tool.check([path])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("bandit")
        assert_that(result.issues_count >= 0).is_true()
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(path)
