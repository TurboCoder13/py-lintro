"""Integration tests for Ruff flake8-annotations (ANN) rule family."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest
from assertpy import assert_that

from lintro.plugins import ToolRegistry


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(lintro_test_mode):
    """Set LINTRO_TEST_MODE=1 and skip config injection for all tests.

    Uses the shared lintro_test_mode fixture from conftest.py which
    sets both LINTRO_TEST_MODE=1 and LINTRO_SKIP_CONFIG_INJECTION=1.

    Args:
        lintro_test_mode: Shared fixture that manages env vars.

    Yields:
        None: This fixture is used for its side effect only.
    """
    yield


def test_annotations_rules_detected() -> None:
    """Ensure Ruff reports ANN-family violations on a known sample file."""
    sample = os.path.abspath(
        "test_samples/tools/python/ruff/ruff_annotations_violations.py",
    )
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "ruff_annotations_case.py")
        shutil.copy(sample, test_file)

        ruff = ToolRegistry.get("ruff")
        ruff.set_options(select=["ANN"], ignore=[])  # only ANN rules, clear any ignore
        result = ruff.check([test_file], {})

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


def test_annotations_rules_with_other_rules() -> None:
    """Ensure ANN rules work alongside other rule families."""
    sample = os.path.abspath(
        "test_samples/tools/python/ruff/ruff_annotations_violations.py",
    )
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "ruff_annotations_mixed.py")
        shutil.copy(sample, test_file)

        ruff = ToolRegistry.get("ruff")
        ruff.set_options(select=["ANN", "F"], ignore=[])  # ANN + pyflakes, clear ignore
        result = ruff.check([test_file], {})

        assert_that(result.success).is_false()
        codes = [getattr(i, "code", "") for i in (result.issues or [])]
        # Should have ANN codes (F codes may not be present in this sample)
        assert_that(any(code.startswith("ANN") for code in codes)).is_true()


def test_annotations_rules_fix_capability() -> None:
    """Test that ANN rules can be fixed automatically where possible."""
    sample = os.path.abspath(
        "test_samples/tools/python/ruff/ruff_annotations_violations.py",
    )
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "ruff_annotations_fix.py")
        shutil.copy(sample, test_file)

        ruff = ToolRegistry.get("ruff")
        ruff.set_options(select=["ANN"], ignore=[])

        # Check initial issues
        initial_result = ruff.check([test_file], {})
        initial_count = len(initial_result.issues or [])

        # Apply fixes
        ruff.fix([test_file], {})

        # Check remaining issues after fix
        final_result = ruff.check([test_file], {})
        final_count = len(final_result.issues or [])

        # Some issues should be fixed (though ANN rules are often not auto-fixable)
        # We mainly verify the fix process doesn't crash and reduces issue count
        assert_that(initial_count).is_greater_than_or_equal_to(final_count)
        # Fix result may be False if issues remain, which is expected for ANN rules
