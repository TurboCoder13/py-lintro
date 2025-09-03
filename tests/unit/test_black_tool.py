from __future__ import annotations

from pathlib import Path

from lintro.tools.implementations.tool_black import BlackTool


def test_black_check_parses_issues(monkeypatch, tmp_path: Path):
    tool = BlackTool()

    # Create a dummy file path
    f = tmp_path / "a.py"
    f.write_text("print('x')\n")

    # Stub file discovery to return our file
    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    # Stub subprocess to emit a would-reformat line in check mode
    def fake_run(cmd, timeout=None, cwd=None):
        if "--check" in cmd:
            return (False, f"would reformat {f.name}\nAll done!\n")
        return (True, "")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    res = tool.check([str(tmp_path)])
    assert res.issues_count == 1
    assert not res.success
    assert res.issues and res.issues[0].file == f.name


def test_black_fix_computes_counts(monkeypatch, tmp_path: Path):
    tool = BlackTool()

    f = tmp_path / "b.py"
    f.write_text("print('y')\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    # Sequence: initial check -> differences, fix -> output unused, final check -> none
    calls = {"n": 0}

    def fake_run(cmd, timeout=None, cwd=None):
        if "--check" in cmd:
            if calls["n"] == 0:
                calls["n"] += 1
                return (False, f"would reformat {f.name}\n")
            else:
                return (True, "All done! 1 file left unchanged.")
        # format phase
        return (True, "reformatted b.py\n")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    res = tool.fix([str(tmp_path)])
    assert res.initial_issues_count == 1
    assert res.fixed_issues_count == 1
    assert res.remaining_issues_count == 0
    assert res.success
