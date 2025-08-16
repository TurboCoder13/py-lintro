from __future__ import annotations

from pathlib import Path

from lintro.utils.config import load_lintro_tool_config


def test_load_lintro_tool_config(tmp_path: Path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
        [tool.lintro]
        [tool.lintro.ruff]
        select = ["E", "F"]
        line_length = 88
        [tool.lintro.prettier]
        single_quote = true
        """
    )
    monkeypatch.chdir(tmp_path)

    ruff_cfg = load_lintro_tool_config("ruff")
    assert ruff_cfg.get("line_length") == 88
    assert ruff_cfg.get("select") == ["E", "F"]

    prettier_cfg = load_lintro_tool_config("prettier")
    assert prettier_cfg.get("single_quote") is True

    missing_cfg = load_lintro_tool_config("yamllint")
    assert missing_cfg == {}
