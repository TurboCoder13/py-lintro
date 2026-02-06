"""Tests for scripts/ci/verify-manifest-tools.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from assertpy import assert_that


def _load_verify_manifest_tools_module() -> ModuleType:
    """Load verify-manifest-tools.py as a module for unit testing."""
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "ci"
        / "verify-manifest-tools.py"
    )
    spec = importlib.util.spec_from_file_location(
        "verify_manifest_tools",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load verify-manifest-tools.py module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tool_command_uses_install_bin_when_provided() -> None:
    """verify-manifest-tools should honor install.bin for executable name."""
    module = _load_verify_manifest_tools_module()

    # Access private function for testing - module loaded dynamically via importlib
    tool_command_fn = module._tool_command  # noqa: SLF001
    cmd = tool_command_fn(
        "astro_check",
        {"type": "npm", "package": "astro", "bin": "astro"},
    )

    assert_that(cmd).is_equal_to(["astro", "--version"])
