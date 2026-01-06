"""Tests for the semantic_release_compute_next utility."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from assertpy import assert_that


def _fake_completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    """Return a fake subprocess.CompletedProcess with the given stdout.

    Args:
        stdout: Standard output string with trailing whitespace stripped.

    Returns:
        subprocess.CompletedProcess: Fake subprocess.CompletedProcess with stdout.
    """
    return subprocess.CompletedProcess(
        args=["git"],
        returncode=0,
        stdout=stdout,
        stderr="",
    )


@pytest.fixture(autouse=True)
def _ensure_repo_root_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure script imports resolve from repository root.

    This avoids issues when tests are invoked from temp directories.

    Args:
        monkeypatch: pytest.MonkeyPatch instance.
    """
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)


def test_run_git_describe_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_git should allow safe describe invocation.

    Args:
        monkeypatch: pytest.MonkeyPatch instance.
    """
    from scripts.ci.maintenance import semantic_release_compute_next as mod

    monkeypatch.setattr(mod.shutil, "which", lambda *_: "/usr/bin/git")  # type: ignore[attr-defined]
    monkeypatch.setattr(
        mod.subprocess,  # type: ignore[attr-defined]
        "run",
        lambda *_, **__: _fake_completed("v1.2.3\n"),
    )

    out = mod.run_git("describe", "--tags", "--abbrev=0", "--match", "v*")
    assert_that(out).is_equal_to("v1.2.3")


def test_run_git_rev_parse_head_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_git should allow 'rev-parse HEAD'.

    Args:
        monkeypatch: pytest.MonkeyPatch instance.
    """
    from scripts.ci.maintenance import semantic_release_compute_next as mod

    monkeypatch.setattr(mod.shutil, "which", lambda *_: "/usr/bin/git")  # type: ignore[attr-defined]
    monkeypatch.setattr(
        mod.subprocess,  # type: ignore[attr-defined]
        "run",
        lambda *_, **__: _fake_completed("abcd123\n"),
    )

    out = mod.run_git("rev-parse", "HEAD")
    assert_that(out).is_equal_to("abcd123")


@pytest.mark.parametrize(
    "args",
    [
        ("log", "HEAD", "--pretty=%s"),
        ("log", "HEAD", "--pretty=%B"),
        ("log", "v1.2.3..HEAD", "--pretty=%s"),
    ],
)
def test_run_git_log_allowed(
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
) -> None:
    """run_git should allow the specific log forms used by the module.

    Args:
        monkeypatch: pytest.MonkeyPatch instance.
        args: Tuple of arguments to pass to run_git.
    """
    from scripts.ci.maintenance import semantic_release_compute_next as mod

    monkeypatch.setattr(mod.shutil, "which", lambda *_: "/usr/bin/git")  # type: ignore[attr-defined]
    monkeypatch.setattr(mod.subprocess, "run", lambda *_, **__: _fake_completed("ok\n"))  # type: ignore[attr-defined]

    out = mod.run_git(*args)
    assert_that(out).is_equal_to("ok")


@pytest.mark.parametrize(
    "args",
    [
        ("status",),
        ("log", "--since=yesterday"),
        ("log", "HEAD; rm -rf /"),
        ("rev-parse", "main"),
    ],
)
def test_run_git_rejects_unsupported_or_unsafe(
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
) -> None:
    """run_git should reject commands/args outside the strict allowlist.

    Args:
        monkeypatch: pytest.MonkeyPatch instance.
        args: Tuple of arguments to pass to run_git.
    """
    from scripts.ci.maintenance import semantic_release_compute_next as mod

    monkeypatch.setattr(mod.shutil, "which", lambda *_: "/usr/bin/git")  # type: ignore[attr-defined]

    # subprocess.run should not be called; keep a guard that would fail if it is
    def _should_not_run(
        *_a: Any,
        **_k: Any,
    ) -> subprocess.CompletedProcess[str]:  # pragma: no cover
        raise AssertionError("subprocess.run must not be invoked for rejected args")

    monkeypatch.setattr(mod.subprocess, "run", _should_not_run)  # type: ignore[attr-defined]

    with pytest.raises(ValueError):
        mod.run_git(*args)
