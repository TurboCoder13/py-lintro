"""Tests for fmt exclusion of non-fixing tools like Bandit.

These tests ensure that format action (fmt) excludes Bandit by default and that
an explicit request for fmt with Bandit yields a helpful error.
"""

import pytest
from assertpy import assert_that

from lintro.utils.tool_executor import _get_tools_to_run


def test_fmt_excludes_bandit_by_default() -> None:
    """fmt should include only tools that can_fix (Bandit excluded)."""
    tools = _get_tools_to_run(tools=None, action="fmt")
    names = {t.name for t in tools}
    assert_that(names).does_not_contain("BANDIT")


def test_fmt_explicit_bandit_raises_error() -> None:
    """Explicit fmt of Bandit should raise a ValueError with helpful message."""
    with pytest.raises(ValueError) as exc:
        _get_tools_to_run(tools="bandit", action="fmt")
    assert_that(str(exc.value)).contains("does not support formatting")
