"""Integration tests for Ruff pep8-naming (N) rule family."""

from __future__ import annotations

import os
import shutil
import tempfile

from assertpy import assert_that

from lintro.tools.implementations.tool_ruff import RuffTool


def test_pep8_naming_rules_detected() -> None:
    """Ensure Ruff reports N-family violations on a known sample file."""
    sample = os.path.abspath("test_samples/ruff_naming_violations.py")
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "ruff_naming_case.py")
        shutil.copy(sample, test_file)

        ruff = RuffTool()
        ruff.set_options(select=["N"])  # only N rules
        result = ruff.check([test_file])

        assert_that(result.success).is_false()
        codes = [getattr(i, "code", "") for i in (result.issues or [])]
        # Expect several representative N-codes
        assert_that(any(code.startswith("N8") for code in codes)).is_true()
        assert_that(
            any(code in {"N802", "N803", "N806", "N815"} for code in codes),
        ).is_true()
