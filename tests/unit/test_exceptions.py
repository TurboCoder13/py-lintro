"""Unit tests for custom exception hierarchy and messages."""

from __future__ import annotations

from assertpy import assert_that

from lintro.exceptions.errors import (
    InvalidToolConfigError,
    InvalidToolOptionError,
    LintroError,
)


def test_custom_exceptions_str_and_inheritance() -> None:
    """Ensure custom exceptions inherit and stringify as expected."""
    base = LintroError("base")
    assert_that(isinstance(base, Exception)).is_true()
    assert_that(str(base)).is_equal_to("base")
    cfg = InvalidToolConfigError("bad config")
    opt = InvalidToolOptionError("bad option")
    assert_that(isinstance(cfg, LintroError)).is_true()
    assert_that(isinstance(opt, LintroError)).is_true()
    assert_that(str(cfg)).contains("bad config")
    assert_that(str(opt)).contains("bad option")
