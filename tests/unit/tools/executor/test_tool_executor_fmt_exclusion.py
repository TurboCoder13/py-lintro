"""Tests for fmt exclusion of non-fixing tools like Bandit.

These tests ensure that format action (fmt) excludes Bandit by default and that
an explicit request for fmt with Bandit yields a helpful error.
"""

import pytest
from assertpy import assert_that

from lintro.utils.execution.tool_configuration import get_tools_to_run


def test_fmt_excludes_bandit_by_default() -> None:
    """Fmt should include only tools that can_fix (Bandit excluded)."""
    tools = get_tools_to_run(tools=None, action="fmt")
    # tools is now a list of string names
    assert_that(tools).does_not_contain("bandit")


def test_fmt_explicit_bandit_raises_error() -> None:
    """Explicit fmt of Bandit should raise a ValueError with helpful message."""
    with pytest.raises(ValueError) as exc:
        get_tools_to_run(tools="bandit", action="fmt")
    assert_that(str(exc.value)).contains("does not support formatting")
