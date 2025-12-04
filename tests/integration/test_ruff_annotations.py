"""Integration tests for Ruff flake8-annotations (ANN) rule family."""

from __future__ import annotations

import os
import shutil
import tempfile

from assertpy import assert_that

from lintro.tools.implementations.tool_ruff import RuffTool


def test_annotations_rules_detected() -> None:
    """Ensure Ruff reports ANN-family violations on a known sample file."""
    # Disable Lintro config injection so we can test specific rule selection
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    try:
        sample = os.path.abspath("test_samples/ruff_annotations_violations.py")
        with tempfile.TemporaryDirectory() as tmp:
            test_file = os.path.join(tmp, "ruff_annotations_case.py")
            shutil.copy(sample, test_file)

            ruff = RuffTool()
            ruff.set_options(select=["ANN"])  # only ANN rules
            result = ruff.check([test_file])

            assert_that(result.success).is_false()
            codes = [getattr(i, "code", "") for i in (result.issues or [])]
            # Expect several representative ANN-codes
            assert_that(any(code.startswith("ANN") for code in codes)).is_true()
            assert_that(
                any(
                    code in {"ANN101", "ANN102", "ANN201", "ANN204", "ANN205", "ANN003"}
                    for code in codes
                ),
            ).is_true()
    finally:
        del os.environ["LINTRO_SKIP_CONFIG_INJECTION"]


def test_annotations_rules_with_other_rules() -> None:
    """Ensure ANN rules work alongside other rule families."""
    # Disable Lintro config injection so we can test specific rule selection
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    try:
        sample = os.path.abspath("test_samples/ruff_annotations_violations.py")
        with tempfile.TemporaryDirectory() as tmp:
            test_file = os.path.join(tmp, "ruff_annotations_mixed.py")
            shutil.copy(sample, test_file)

            ruff = RuffTool()
            ruff.set_options(select=["ANN", "F"])  # ANN + pyflakes errors
            result = ruff.check([test_file])

            assert_that(result.success).is_false()
            codes = [getattr(i, "code", "") for i in (result.issues or [])]
            # Should have ANN codes (F codes may not be present in this sample)
            assert_that(any(code.startswith("ANN") for code in codes)).is_true()
    finally:
        del os.environ["LINTRO_SKIP_CONFIG_INJECTION"]


def test_annotations_rules_fix_capability() -> None:
    """Test that ANN rules can be fixed automatically where possible."""
    # Disable Lintro config injection so we can test specific rule selection
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    try:
        sample = os.path.abspath("test_samples/ruff_annotations_violations.py")
        with tempfile.TemporaryDirectory() as tmp:
            test_file = os.path.join(tmp, "ruff_annotations_fix.py")
            shutil.copy(sample, test_file)

            ruff = RuffTool()
            ruff.set_options(select=["ANN"])

            # Check initial issues
            initial_result = ruff.check([test_file])
            initial_count = len(initial_result.issues or [])

            # Apply fixes
            ruff.fix([test_file])

            # Check remaining issues after fix
            final_result = ruff.check([test_file])
            final_count = len(final_result.issues or [])

            # Some issues should be fixed (though ANN rules are often not auto-fixable)
            # We mainly verify the fix process doesn't crash and reduces issue count
            assert_that(initial_count).is_greater_than_or_equal_to(final_count)
            # Fix result may be False if issues remain, which is expected for ANN rules
    finally:
        del os.environ["LINTRO_SKIP_CONFIG_INJECTION"]
