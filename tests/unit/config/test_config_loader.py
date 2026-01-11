"""Unit tests for lintro configuration loaders from pyproject.toml."""

from __future__ import annotations

from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.utils.config import (
    _find_pyproject,
    load_lintro_tool_config,
    load_pyproject,
)


def test_load_lintro_tool_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Load tool-specific config sections from pyproject.

    Args:
        tmp_path: Temporary directory for pyproject creation.
        monkeypatch: Pytest monkeypatch to chdir into temp dir.
    """
    # Clear both LRU caches to ensure we load from the test directory
    load_pyproject.cache_clear()
    _find_pyproject.cache_clear()

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        (
            "[tool.lintro]\n"
            "[tool.lintro.ruff]\n"
            'select = ["E", "F"]\n'
            "line_length = 88\n"
            "[tool.lintro.prettier]\n"
            "single_quote = true\n"
        ),
    )
    monkeypatch.chdir(tmp_path)
    ruff_cfg = load_lintro_tool_config("ruff")
    assert_that(ruff_cfg.get("line_length")).is_equal_to(88)
    assert_that(ruff_cfg.get("select")).is_equal_to(["E", "F"])
    prettier_cfg = load_lintro_tool_config("prettier")
    assert_that(prettier_cfg.get("single_quote") is True).is_true()
    missing_cfg = load_lintro_tool_config("yamllint")
    assert_that(missing_cfg).is_equal_to({})


def test_config_loader_handles_missing_and_malformed_pyproject(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validate loaders handle missing and malformed pyproject files.

    Args:
        tmp_path: Temporary directory used to simulate project roots.
        monkeypatch: Pytest monkeypatch fixture for chdir and environment.
    """
    # Clear both LRU caches to ensure we load from the test directory
    load_pyproject.cache_clear()
    _find_pyproject.cache_clear()

    from lintro.utils import config as cfg

    # 1) Missing pyproject.toml
    monkeypatch.chdir(tmp_path)
    assert_that(cfg.load_lintro_tool_config("ruff")).is_equal_to({})
    assert_that(cfg.load_post_checks_config()).is_equal_to({})

    # 2) Malformed pyproject.toml should be handled gracefully
    (tmp_path / "pyproject.toml").write_text("not: [valid\n")
    assert_that(cfg.load_lintro_tool_config("ruff")).is_equal_to({})
    assert_that(cfg.load_post_checks_config()).is_equal_to({})
