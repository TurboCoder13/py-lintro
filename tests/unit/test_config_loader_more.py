"""Extra tests for config loader covering post_checks happy path."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.config import load_post_checks_config


def test_load_post_checks_config_present(tmp_path: Path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        (
            "[tool.lintro.post_checks]\n"
            "enabled = true\n"
            'tools = ["black"]\n'
            "enforce_failure = true\n"
        ),
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_post_checks_config()
    assert_that(cfg.get("enabled") is True).is_true()
    assert_that(cfg.get("tools")).is_equal_to(["black"])
    assert_that(cfg.get("enforce_failure") is True).is_true()
