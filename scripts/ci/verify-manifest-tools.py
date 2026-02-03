#!/usr/bin/env python3
"""Verify installed tools against the manifest inside a container image."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from typing import Any

_VERSION_RE = re.compile(r"\d+(?:\.\d+){1,3}")


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        )
        output = stdout + stderr
        if not output:
            output = "Command timed out"
        return 124, output.strip()
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def _parse_version(output: str, tool_name: str) -> str | None:
    if tool_name == "clippy":
        match = re.search(r"clippy\s+0\.1\.(\d+)", output, re.IGNORECASE)
        if match:
            return f"1.{match.group(1)}.0"
    match = _VERSION_RE.search(output)
    if not match:
        return None
    return match.group(0)


def _tool_command(tool_name: str, install: dict[str, Any]) -> list[str]:
    # TODO: support install["version_command"] to allow custom invocations.
    bin_name = install.get("bin") if isinstance(install, dict) else None

    if tool_name == "cargo_audit":
        return ["cargo", "audit", "--version"]
    if tool_name == "clippy":
        return ["cargo", "clippy", "--version"]
    if tool_name == "markdownlint":
        return [bin_name or "markdownlint-cli2", "--version"]
    if tool_name == "gitleaks":
        return [bin_name or "gitleaks", "version"]
    if tool_name == "rustfmt":
        return [bin_name or "rustfmt", "--version"]
    if tool_name == "shellcheck":
        return [bin_name or "shellcheck", "--version"]
    if tool_name == "taplo":
        return [bin_name or "taplo", "--version"]
    if tool_name == "actionlint":
        return [bin_name or "actionlint", "--version"]

    # Default: use package binary name if provided, else tool name.
    return [bin_name or tool_name, "--version"]


def _load_manifest(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError("manifest tools must be a list")
    return [t for t in tools if isinstance(t, dict)]


def _iter_tools(
    tools: list[dict[str, Any]],
    tiers: Iterable[str],
) -> list[dict[str, Any]]:
    allowed = {t.strip() for t in tiers if t.strip()}
    selected = []
    for tool in tools:
        tier = tool.get("tier", "tools")
        if tier in allowed:
            selected.append(tool)
    return selected


def main() -> int:
    """Verify tools in manifest.json are installed with correct versions."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default=os.environ.get("LINTRO_MANIFEST", "lintro/tools/manifest.json"),
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--tiers",
        default=os.environ.get("LINTRO_MANIFEST_TIERS", "tools"),
        help="Comma-separated tiers to verify (default: tools)",
    )
    args = parser.parse_args()

    tiers = [t.strip() for t in args.tiers.split(",")]
    tools = _iter_tools(_load_manifest(args.manifest), tiers)

    failures: list[str] = []
    for tool in tools:
        name = str(tool.get("name", "")).strip()
        expected = str(tool.get("version", "")).strip()
        install = tool.get("install", {})
        if not name or not expected:
            failures.append(f"{name or '<unknown>'}: missing name or version")
            continue

        cmd = _tool_command(name, install if isinstance(install, dict) else {})
        code, output = _run(cmd)
        if code != 0:
            failures.append(f"{name}: command failed ({' '.join(cmd)})")
            continue

        actual = _parse_version(output, name)
        if not actual:
            failures.append(f"{name}: failed to parse version from '{output}'")
            continue

        if actual != expected:
            failures.append(
                f"{name}: version mismatch (expected {expected}, got {actual})",
            )

    if failures:
        print("Tool verification failed:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print(f"Verified {len(tools)} tool(s) against manifest tiers: {', '.join(tiers)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
