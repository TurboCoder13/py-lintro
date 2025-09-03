from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.utils.config import load_lintro_tool_config


def test_load_lintro_tool_config(tmp_path: Path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        (
            "\n        [tool.lintro]\n"
            "        [tool.lintro.ruff]\n"
            '        select = ["E", "F"]\n'
            "        line_length = 88\n"
            "        [tool.lintro.prettier]\n"
            "        single_quote = true\n"
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
