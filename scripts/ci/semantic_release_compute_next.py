#!/usr/bin/env python3
"""Compute the next semantic version for releases.

This script computes the next version based on Conventional Commits since the
last baseline (git tag v*, or the last "chore(release): prepare X.Y.Z" commit,
or the current version declared in pyproject.toml). It writes
"next_version=<semver>" to GITHUB_OUTPUT when available.

It honors the environment variable MAX_BUMP. When MAX_BUMP="minor", any major
increments are clamped down to a minor bump of the current major version.

Usage:
  uv run python scripts/ci/semantic_release_compute_next.py [--print-only]

"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass
class ComputeResult:
    """Result of computing next version.

    Attributes:
        base_ref: Git ref used as baseline (tag or commit)
        base_version: Base semantic version string
        next_version: Computed next semantic version string or empty string
        has_breaking: Whether breaking commits were detected
        has_feat: Whether feature commits were detected
        has_fix_or_perf: Whether fix/perf commits were detected
    """

    base_ref: str
    base_version: str
    next_version: str
    has_breaking: bool
    has_feat: bool
    has_fix_or_perf: bool


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return (result.stdout or "").strip()


def read_last_tag() -> str:
    return run_git("describe", "--tags", "--abbrev=0", "--match", "v*")


def read_last_prepare_commit() -> Tuple[str, str]:
    sha = run_git(
        "log",
        "--grep=^chore(release): prepare ",
        "--pretty=format:%h",
        "-n",
        "1",
        "--no-merges",
    )
    if not sha:
        return "", ""
    subject = run_git("log", "-1", "--pretty=format:%s", sha)
    m = re.search(r"prepare (\d+\.\d+\.\d+)", subject)
    return sha, (m.group(1) if m else "")


def read_pyproject_version() -> str:
    path = Path("pyproject.toml")
    if not path.exists():
        return ""
    for line in path.read_text().splitlines():
        m = re.match(r"^version\s*=\s*\"(\d+\.\d+\.\d+)\"", line.strip())
        if m:
            return m.group(1)
    return ""


def parse_semver(version: str) -> Tuple[int, int, int]:
    m = SEMVER_RE.match(version)
    if not m:
        return 0, 0, 0
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def detect_commit_types(base_ref: str) -> Tuple[bool, bool, bool]:
    log_range = f"{base_ref}..HEAD" if base_ref else "HEAD"
    subjects = run_git("log", log_range, "--pretty=%s")
    bodies = run_git("log", log_range, "--pretty=%B")
    has_breaking = bool(
        re.search(r"^[a-z][^:!]*!:", subjects, flags=re.MULTILINE)
        or re.search(r"^BREAKING CHANGE:", bodies, flags=re.MULTILINE)
    )
    has_feat = bool(re.search(r"^feat(\(|:)|^feat!", subjects, flags=re.MULTILINE))
    has_fix_or_perf = bool(
        re.search(r"^(fix|perf)(\(|:)|^(fix|perf)!", subjects, flags=re.MULTILINE)
    )
    return has_breaking, has_feat, has_fix_or_perf


def compute_next_version(base_version: str, breaking: bool, feat: bool, fix: bool) -> str:
    major, minor, patch = parse_semver(base_version)
    if breaking:
        major += 1
        minor = 0
        patch = 0
    elif feat:
        minor += 1
        patch = 0
    elif fix:
        patch += 1
    else:
        return ""
    return f"{major}.{minor}.{patch}"


def clamp_to_minor(base_version: str, next_version: str, max_bump: Optional[str]) -> str:
    if not base_version or not next_version:
        return next_version
    if (max_bump or "").lower() != "minor":
        return next_version
    bmaj, bmin, _ = parse_semver(base_version)
    nmaj, _, _ = parse_semver(next_version)
    if nmaj > bmaj:
        return f"{bmaj}.{bmin + 1}.0"
    return next_version


def compute() -> ComputeResult:
    # Enterprise policy: tags are the single source of truth.
    # Require an existing v*-prefixed tag as the baseline; fail if missing.
    last_tag = read_last_tag()
    if not last_tag:
        raise RuntimeError(
            "No v*-prefixed release tag found. Tag the last release (e.g., v0.4.0) "
            "before computing the next version."
        )
    base_ref = last_tag
    base_version = last_tag.lstrip("v")

    breaking, feat, fix = detect_commit_types(base_ref)
    next_version = compute_next_version(base_version, breaking, feat, fix)
    next_version = clamp_to_minor(base_version, next_version, os.getenv("MAX_BUMP"))
    return ComputeResult(
        base_ref=base_ref,
        base_version=base_version,
        next_version=next_version,
        has_breaking=breaking,
        has_feat=feat,
        has_fix_or_perf=fix,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute next semantic version and write to GITHUB_OUTPUT"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print next version to stdout instead of writing GITHUB_OUTPUT",
    )
    args = parser.parse_args()

    try:
        result = compute()
    except RuntimeError as exc:
        msg = str(exc)
        print(msg)
        raise SystemExit(2)

    print(
        f"Base: {result.base_ref or '<none>'} ({result.base_version or 'unknown'})\n"
        f"Detected: breaking={result.has_breaking} feat={result.has_feat} fix/perf={result.has_fix_or_perf}"
    )

    if args.print_only or not os.getenv("GITHUB_OUTPUT"):
        print(f"next_version={result.next_version}")
        return

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write(f"next_version={result.next_version}\n")


if __name__ == "__main__":
    main()


