"""Integration tests validating Ruff/Black policy behavior."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest
from assertpy import assert_that

from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_ruff import RuffTool


@pytest.fixture(autouse=True)
def auto_skip_config_injection(skip_config_injection):
    """Disable Lintro config injection for all tests in this module.

    Uses the shared skip_config_injection fixture from conftest.py.

    Args:
        skip_config_injection: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_com812_reported_by_ruff_with_black_present() -> None:
    """Ruff should report COM812 even when Black is present as formatter.

    Create a list literal missing a trailing comma in multi-line form and
    verify that Ruff flags COM812. This ensures Ruff keeps strict linting
    while Black can still be used for formatting in post-checks.
    """
    content = (
        "my_list = [\n"
        "    1,\n"
        "    2,\n"
        "    3\n"  # missing trailing comma
        "]\n"
        "print(len(my_list))\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, "com812_case.py")
        _write(file_path, content)

        ruff = RuffTool()
        # Ensure COM rules selected and formatting check off for lint-only
        ruff.set_options(select=["COM"], format_check=False)
        result = ruff.check([file_path])
        assert_that(result.success).is_false()
        # Ensure COM812 is among reported issues
        codes = [getattr(i, "code", "") for i in (result.issues or [])]
        assert_that("COM812" in codes).is_true()


def test_e501_wrapped_by_black_then_clean_under_ruff() -> None:
    """Black should wrap long lines safely so Ruff no longer reports E501.

    Create a safely breakable long line (function call with many keyword args),
    let Black apply formatting, then verify Ruff no longer reports E501.
    """
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.abspath("test_samples/ruff_black_e501_wrappable.py")
        file_path = os.path.join(tmp, "e501_case.py")
        shutil.copy(src, file_path)

        # Verify Ruff detects formatting issue (long line) before Black
        ruff = RuffTool()
        ruff.set_options(select=["E"], format_check=True, line_length=88)
        pre = ruff.check([file_path])
        # RuffFormatIssue does not have code; verify via issue type and count
        assert_that(
            any(
                hasattr(i, "file") and not hasattr(i, "code")
                for i in (pre.issues or [])
            ),
        ).is_true()

        # Apply Black formatting (do not rely on fixed count across platforms)
        black = BlackTool()
        _ = black.fix([file_path])

        # After Black, Ruff should no longer report formatting issue for this case
        post = ruff.check([file_path])
        # After formatting, there should be no RuffFormatIssue entries
        assert_that(
            any(
                hasattr(i, "file") and not hasattr(i, "code")
                for i in (post.issues or [])
            ),
        ).is_false()
