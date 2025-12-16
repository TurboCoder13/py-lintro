"""Unit tests for Clippy tool integration."""

from __future__ import annotations

from pathlib import Path

from lintro.tools.implementations.tool_clippy import ClippyTool


def test_clippy_check_parses_issues(monkeypatch, tmp_path: Path) -> None:
    """Ensure check mode parses Clippy JSON output correctly.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = ClippyTool()

    # Create a dummy Rust file
    rust_file = tmp_path / "src" / "lib.rs"
    rust_file.parent.mkdir()
    rust_file.write_text("fn main() { return 42; }\n")

    # Create Cargo.toml
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"\n')

    # Stub file discovery to return our file
    monkeypatch.setattr(
        "lintro.tools.implementations.tool_clippy.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [
            str(rust_file),
        ],
        raising=True,
    )

    # Stub subprocess to emit Clippy JSON output
    clippy_output = (
        '{"reason":"compiler-message","message":{"code":{"code":"clippy::needless_return"},'
        '"level":"warning","message":"unneeded `return` statement",'
        '"spans":[{"file_name":"src/lib.rs","line_start":1,"line_end":1,'
        '"column_start":15,"column_end":21}]}}\n'
    )

    def fake_run(cmd, timeout=None, cwd=None):
        if "clippy" in cmd and "--fix" not in cmd:
            return (False, clippy_output)
        return (True, "")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    res = tool.check([str(tmp_path)])
    assert res.issues_count == 1
    assert not res.success
    assert res.issues and res.issues[0].code == "clippy::needless_return"


def test_clippy_check_no_cargo_toml(monkeypatch, tmp_path: Path) -> None:
    """Skip when no Cargo.toml is found.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = ClippyTool()

    rust_file = tmp_path / "lib.rs"
    rust_file.write_text("fn main() {}\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_clippy.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [
            str(rust_file),
        ],
        raising=True,
    )

    res = tool.check([str(tmp_path)])
    assert res.success
    assert res.issues_count == 0
    assert "No Cargo.toml found" in res.output or "skipping" in res.output.lower()


def test_clippy_fix_computes_counts(monkeypatch, tmp_path: Path) -> None:
    """Ensure fix mode computes initial/fixed/remaining issue counts.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = ClippyTool()

    rust_file = tmp_path / "src" / "lib.rs"
    rust_file.parent.mkdir()
    rust_file.write_text("fn main() { return 42; }\n")

    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"\n')

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_clippy.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [
            str(rust_file),
        ],
        raising=True,
    )

    calls = {"n": 0}

    initial_output = (
        '{"reason":"compiler-message","message":{"code":{"code":"clippy::needless_return"},'
        '"level":"warning","message":"unneeded return",'
        '"spans":[{"file_name":"src/lib.rs",'
        '"line_start":1,"line_end":1,"column_start":15,"column_end":21}]}}\n'
    )

    def fake_run(cmd, timeout=None, cwd=None):
        if "clippy" in cmd:
            if "--fix" in cmd:
                calls["n"] += 1
                return (True, "")
            # Check mode
            if calls["n"] == 0:
                calls["n"] += 1
                return (False, initial_output)
            else:
                # After fix, no issues
                return (True, "")
        return (True, "")

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


def test_clippy_check_no_rust_files(monkeypatch, tmp_path: Path) -> None:
    """Handle case when no Rust files are found.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = ClippyTool()

    python_file = tmp_path / "main.py"
    python_file.write_text("print('hello')\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_clippy.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [],
        raising=True,
    )

    res = tool.check([str(tmp_path)])
    assert res.success
    assert res.issues_count == 0
    assert "No Rust files" in res.output
