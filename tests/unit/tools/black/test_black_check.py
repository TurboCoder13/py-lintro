"""Unit tests for Black tool integration and option wiring."""

from __future__ import annotations

from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.parsers.black.black_issue import BlackIssue
from lintro.tools.implementations.tool_black import BlackTool


def test_black_check_parses_issues(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ensure check mode recognizes would-reformat output as an issue.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = BlackTool()

    # Create a dummy file path
    f = tmp_path / "a.py"
    f.write_text("print('x')\n")

    # Stub file discovery to return our file (mock in path_filtering module)
    monkeypatch.setattr(
        "lintro.utils.path_filtering.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    # Stub subprocess to emit a would-reformat line in check mode
    def fake_run(
        cmd: list[str],
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        if "--check" in cmd:
            return (False, f"would reformat {f.name}\nAll done!\n")
        return (True, "")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    res = tool.check([str(tmp_path)])
    assert_that(res.issues_count).is_equal_to(1)
    assert_that(res.success).is_false()
    assert_that(res.issues).is_not_empty()
    assert_that(res.issues).is_not_none()
    issues = res.issues
    assert_that(issues).is_not_none()
    if issues is None:
        pytest.fail("issues should not be None")
    first_issue = issues[0]
    assert_that(isinstance(first_issue, BlackIssue)).is_true()
    if not isinstance(first_issue, BlackIssue):
        pytest.fail("first_issue should be BlackIssue")
    assert_that(first_issue.file).is_equal_to(f.name)


def test_black_fix_computes_counts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ensure fix mode computes initial/fixed/remaining issue counts.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = BlackTool()

    f = tmp_path / "b.py"
    f.write_text("print('y')\n")

    monkeypatch.setattr(
        "lintro.utils.path_filtering.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    # Sequence: initial check -> differences, fix -> output unused, final check -> none
    calls = {"n": 0}

    def fake_run(
        cmd: list[str],
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
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
    assert_that(res.initial_issues_count).is_equal_to(1)
    assert_that(res.fixed_issues_count).is_equal_to(1)
    assert_that(res.remaining_issues_count).is_equal_to(0)
    assert_that(res.success).is_true()


def test_black_options_build_line_length_and_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify line-length and target version flags are passed in check mode.

    When no Lintro config is found, Black should use CLI flags.
    When Lintro config is found, Black should use --config flag.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    # Clear Lintro config cache to ensure no config file influences this test
    from lintro.config import clear_config_cache

    clear_config_cache()

    tool = BlackTool()

    f = tmp_path / "opt.py"
    f.write_text("print('opt')\n")

    monkeypatch.setattr(
        "lintro.utils.path_filtering.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    captured: dict[str, list[str]] = {}

    def fake_run(
        cmd: list[str],
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        captured["cmd"] = cmd
        # Simulate no differences so command content is what we validate
        return (True, "All done! 1 file left unchanged.")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    # Mock _should_use_lintro_config to return False (no lintro config found)
    from lintro.tools.core import config_injection

    monkeypatch.setattr(
        config_injection,
        "_should_use_lintro_config",
        lambda tool_name, lintro_config=None: False,
    )

    tool.set_options(line_length=100, target_version="py313")
    _ = tool.check([str(tmp_path)])
    cmd = captured["cmd"]
    # Ensure flags are present (CLI mode when no lintro config)
    assert_that(cmd).contains("--check")
    assert_that(cmd).contains("--line-length")
    assert_that(cmd).contains("100")
    assert_that(cmd).contains("--target-version")
    assert_that(cmd).contains("py313")


def test_black_options_include_fast_and_preview(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify fast and preview flags are honored in check mode.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = BlackTool()

    f = tmp_path / "fastprev.py"
    f.write_text("print('x')\n")

    monkeypatch.setattr(
        "lintro.utils.path_filtering.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    captured: dict[str, list[str]] = {}

    def fake_run(
        cmd: list[str],
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        captured["cmd"] = cmd
        return (True, "All done! 1 file left unchanged.")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    tool.set_options(fast=True, preview=True)
    _ = tool.check([str(tmp_path)])
    captured["cmd"]
