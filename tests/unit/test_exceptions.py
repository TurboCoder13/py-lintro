from __future__ import annotations

from lintro.exceptions.errors import (
    InvalidToolConfigError,
    InvalidToolOptionError,
    LintroError,
)


def test_custom_exceptions_str_and_inheritance():
    base = LintroError("base")
    assert isinstance(base, Exception)
    assert str(base) == "base"

    cfg = InvalidToolConfigError("bad config")
    opt = InvalidToolOptionError("bad option")
    assert isinstance(cfg, LintroError)
    assert isinstance(opt, LintroError)
    assert "bad config" in str(cfg)
    assert "bad option" in str(opt)
