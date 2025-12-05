"""Integration tests for Ruff flake8-annotations (ANN) rule family."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest
from assertpy import assert_that

from lintro.tools.implementations.tool_ruff import RuffTool


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env():
    """Set LINTRO_TEST_MODE=1 for all tests in this module.

    This ensures ruff uses --isolated flag when config injection is skipped,
    preventing local pyproject.toml from interfering with test-specific rules.

    Yields:
        None: This fixture is used for its side effect only.
    """
    old = os.environ.get("LINTRO_TEST_MODE")
    os.environ["LINTRO_TEST_MODE"] = "1"
    yield
    if old is not None:
        os.environ["LINTRO_TEST_MODE"] = old
    else:
        os.environ.pop("LINTRO_TEST_MODE", None)


def test_annotations_rules_detected() -> None:
    """Ensure Ruff reports ANN-family violations on a known sample file."""
    # Disable Lintro config injection so we can test specific rule selection
    original = os.environ.get("LINTRO_SKIP_CONFIG_INJECTION")
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
        if original is None:
            os.environ.pop("LINTRO_SKIP_CONFIG_INJECTION", None)
        else:
            os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = original


def test_annotations_rules_with_other_rules() -> None:
    """Ensure ANN rules work alongside other rule families."""
    # Disable Lintro config injection so we can test specific rule selection
    original = os.environ.get("LINTRO_SKIP_CONFIG_INJECTION")
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
        if original is None:
            os.environ.pop("LINTRO_SKIP_CONFIG_INJECTION", None)
        else:
            os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = original


def test_annotations_rules_fix_capability() -> None:
    """Test that ANN rules can be fixed automatically where possible."""
    # Disable Lintro config injection so we can test specific rule selection
    original = os.environ.get("LINTRO_SKIP_CONFIG_INJECTION")
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
        if original is None:
            os.environ.pop("LINTRO_SKIP_CONFIG_INJECTION", None)
        else:
            os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = original
