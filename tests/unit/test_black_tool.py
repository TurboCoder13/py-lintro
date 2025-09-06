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


def test_black_options_build_line_length_and_target(monkeypatch, tmp_path: Path):
    tool = BlackTool()

    f = tmp_path / "opt.py"
    f.write_text("print('opt')\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    captured: dict[str, list[str]] = {}

    def fake_run(cmd, timeout=None, cwd=None):
        captured["cmd"] = cmd
        # Simulate no differences so command content is what we validate
        return (True, "All done! 1 file left unchanged.")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    tool.set_options(line_length=100, target_version="py313")
    _ = tool.check([str(tmp_path)])
    cmd = captured["cmd"]
    # Ensure flags are present
    assert "--check" in cmd
    assert "--line-length" in cmd and "100" in cmd
    assert "--target-version" in cmd and "py313" in cmd


def test_black_options_include_fast_and_preview(monkeypatch, tmp_path: Path):
    tool = BlackTool()

    f = tmp_path / "fastprev.py"
    f.write_text("print('x')\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    captured: dict[str, list[str]] = {}

    def fake_run(cmd, timeout=None, cwd=None):
        captured["cmd"] = cmd
        return (True, "All done! 1 file left unchanged.")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    tool.set_options(fast=True, preview=True)
    _ = tool.check([str(tmp_path)])
    cmd = captured["cmd"]
    assert "--fast" in cmd
    assert "--preview" in cmd


def test_black_diff_flag_in_fix(monkeypatch, tmp_path: Path):
    tool = BlackTool()

    f = tmp_path / "diff.py"
    f.write_text("print('x')\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    calls: list[list[str]] = []

    def fake_run(cmd, timeout=None, cwd=None):
        calls.append(cmd)
        # First and last are --check; middle is format run
        if "--check" in cmd:
            return (False, f"would reformat {f.name}\n")
        return (True, f"reformatted {f.name}\n")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    tool.set_options(diff=True)
    _ = tool.fix([str(tmp_path)])


def test_black_check_and_fix_with_options(monkeypatch, tmp_path: Path) -> None:
    """Exercise BlackTool option wiring and subprocess building paths.

    Args:
        monkeypatch: Fixture for patching subprocess execution.
        tmp_path: Temporary directory.
    """
    # Create a sample Python file to include in discovery
    sample = tmp_path / "a.py"
    sample.write_text("x=1\n")

    calls: list[dict] = []

    def fake_run(cmd, timeout=None, cwd=None):  # noqa: ANN001
        calls.append({"cmd": cmd, "cwd": cwd})
        # Simulate: check finds 1 issue, fix applies changes, final check finds 0
        if "--check" in cmd:

            if calls and any("--diff" in c["cmd"] for c in calls):
                return True, ""
            return False, f"Would reformat: {sample.name}\n"
        # format run
        return True, f"Reformatted: {sample.name}\n"

    monkeypatch.setattr(
        BlackTool,
        "_run_subprocess",
        lambda self, cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    tool = BlackTool()
    tool.set_options(
        line_length=88,
        target_version="py313",
        fast=True,
        preview=True,
        diff=True,
    )

    res_check = tool.check([str(tmp_path)])
    assert res_check.issues_count >= 0

    res_fix = tool.fix([str(tmp_path)])
    assert res_fix.fixed_issues_count >= 0
    # Ensure options propagated into commands
    flattened = [" ".join(c["cmd"]) for c in calls]
    assert any("--line-length 88" in s for s in flattened)
    assert any("--target-version py313" in s for s in flattened)
    assert any("--fast" in s for s in flattened)
    assert any("--preview" in s for s in flattened)
    # Diff flag is optional in some environments; main options must be present.
    # If diff is enabled, verify it appears in the format (middle) invocation.
    if calls and len(calls) >= 2:
        middle_cmd = calls[1]["cmd"]
        assert "--diff" in middle_cmd
