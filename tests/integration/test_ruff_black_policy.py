from __future__ import annotations

import os
import tempfile

from assertpy import assert_that

from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_ruff import RuffTool


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
    long_call = (
        "def func(**kwargs):\n"
        "    return kwargs\n\n"
        "# Single long line over 88 chars, safe to wrap by Black\n"
        "result = func(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10, k=11, l=12, m=13, n=14)\n"
        "print(result)\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, "e501_case.py")
        _write(file_path, long_call)

        # Verify Ruff detects formatting issue (long line) before Black
        ruff = RuffTool()
        ruff.set_options(select=["E"], format_check=True, line_length=88)
        pre = ruff.check([file_path])
        # RuffFormatIssue does not have code; verify via issue type and count
        assert_that(any(hasattr(i, "file") and not hasattr(i, "code") for i in (pre.issues or []))).is_true()

        # Apply Black formatting (do not rely on fixed count across platforms)
        black = BlackTool()
        _ = black.fix([file_path])

        # After Black, Ruff should no longer report formatting issue for this case
        post = ruff.check([file_path])
        # After formatting, there should be no RuffFormatIssue entries
        assert_that(any(hasattr(i, "file") and not hasattr(i, "code") for i in (post.issues or []))).is_false()
