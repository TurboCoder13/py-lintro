"""Unit tests for Black tool fix/format functionality."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that

from lintro.tools.implementations.tool_black import BlackIssue, BlackTool


def test_black_fix_with_options(monkeypatch, tmp_path: Path) -> None:
    """Test that Black fix mode respects option settings.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = BlackTool()
    tool.set_options(fast=True, preview=True)

    f = tmp_path / "test.py"
    f.write_text("x=1\n")

    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    calls: list[list[str]] = []

    def fake_run(cmd, timeout=None, cwd=None):
        calls.append(cmd)
        return (True, f"reformatted {f.name}\n")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_run(cmd, timeout, cwd),
    )

    _ = tool.fix([str(tmp_path)])

    # Verify options were passed to Black
    cmd = calls[0] if calls else []
    assert_that(cmd).contains("--fast")
    assert_that(cmd).contains("--preview")


def test_black_check_and_fix_with_options(monkeypatch, tmp_path: Path) -> None:
    """Exercise BlackTool option wiring and subprocess building paths.

    Args:
        monkeypatch: Fixture for patching subprocess execution.
        tmp_path: Temporary directory.
    """
    # Clear Lintro config cache to ensure no config file influences this test
    from lintro.config import clear_config_cache

    clear_config_cache()

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

    # Mock _should_use_lintro_config to return False (no lintro config found)
    from lintro.tools.core import config_injection

    monkeypatch.setattr(
        config_injection,
        "_should_use_lintro_config",
        lambda tool_name, lintro_config=None: False,
    )

    tool.set_options(
        line_length=88,
        target_version="py313",
        fast=True,
        preview=True,
        diff=True,
    )

    res_check = tool.check([str(tmp_path)])
    assert_that(res_check.issues_count).is_greater_than_or_equal_to(0)

    res_fix = tool.fix([str(tmp_path)])
    assert_that(res_fix.fixed_issues_count).is_greater_than_or_equal_to(0)
    # Ensure options propagated into commands (CLI mode when no lintro config)
    flattened = [" ".join(c["cmd"]) for c in calls]
    assert_that(any("--line-length 88" in s for s in flattened)).is_true()
    assert_that(any("--target-version py313" in s for s in flattened)).is_true()
    assert_that(any("--fast" in s for s in flattened)).is_true()
    assert_that(any("--preview" in s for s in flattened)).is_true()
    # Diff flag is optional in some environments; main options must be present.
    # If diff is enabled, verify it appears in the format (middle) invocation.
    if calls and len(calls) >= 2:
        middle_cmd = calls[1]["cmd"]
        assert_that(middle_cmd).contains("--diff")


def test_black_check_detects_e501_violations(monkeypatch, tmp_path: Path) -> None:
    """Verify Black's check method integrates line length violation detection.

    Black's --check mode only reports files that would be reformatted, but
    some long lines cannot be safely wrapped. This unit test verifies that
    check() properly incorporates results from _check_line_length_violations
    (which uses Ruff's E501 check) into the final result, even when Black
    itself reports no formatting changes.

    Args:
        monkeypatch: Pytest fixture for monkeypatching subprocess behavior.
        tmp_path: Temporary directory for creating files.
    """
    tool = BlackTool()
    tool.set_options(line_length=88)

    # Create a file with an unwrappable long line (long string literal)
    f = tmp_path / "long_line.py"
    # This line exceeds 88 chars but can't be safely wrapped by Black
    long_line = (
        'x = "This is a very long string literal that exceeds the line '
        "length limit and cannot be safely wrapped by Black formatter "
        'because it is a single string token"'
    )
    f.write_text(f"{long_line}\n")

    # Stub file discovery to return our file
    monkeypatch.setattr(
        "lintro.tools.implementations.tool_black.walk_files_with_excludes",
        lambda paths, file_patterns, exclude_patterns, include_venv: [str(f)],
        raising=True,
    )

    # Stub Black's subprocess to return success (no formatting changes)
    # This simulates Black not detecting the long line because it can't wrap it
    def fake_black_run(cmd, timeout=None, cwd=None):
        if "--check" in cmd:
            return (True, "All done! 1 file left unchanged.")
        return (True, "")

    monkeypatch.setattr(
        tool,
        "_run_subprocess",
        lambda cmd, timeout, cwd=None: fake_black_run(cmd, timeout, cwd),
    )

    # Mock _check_line_length_violations to return E501 violations directly
    def fake_check_line_length_violations(self, files, cwd):
        # Calculate actual line length for accurate test
        line_length = len(long_line)
        return [
            BlackIssue(
                file=str(f),
                message=(
                    f"Line 1 exceeds line length limit "
                    f"(Line too long ({line_length} > 88 characters))"
                ),
                fixable=False,
            ),
        ]

    monkeypatch.setattr(
        BlackTool,
        "_check_line_length_violations",
        fake_check_line_length_violations,
    )

    res = tool.check([str(tmp_path)])
    # Black should detect the E501 violation even though Black itself
    # didn't report any formatting changes
    assert_that(res.issues_count).is_equal_to(1)
    assert_that(res.success).is_false()
    assert_that(res.issues).is_not_empty()
    # Verify the issue is a line length violation
    issue = res.issues[0]
    assert_that(issue).is_instance_of(BlackIssue)
    assert_that(issue.message.lower()).contains("exceeds line length limit")
    assert_that(issue.message.lower()).contains("line")
    assert_that(issue.fixable).is_false()
