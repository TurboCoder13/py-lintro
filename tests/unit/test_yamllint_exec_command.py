"""Unit tests for yamllint executable resolution.

These tests ensure that BaseTool._get_executable_command chooses the
correct invocation strategy for yamllint so that Docker and local runs
behave consistently.
"""

from __future__ import annotations

import types

import pytest

from lintro.tools.implementations.tool_yamllint import YamllintTool


@pytest.fixture()
def yamllint_tool() -> YamllintTool:
    """Provide a YamllintTool instance for executable resolution tests.

    Returns:
        YamllintTool: Configured YamllintTool instance.
    """
    return YamllintTool()


def _make_fake_shutil(which_map: dict[str, str | None]) -> types.SimpleNamespace:
    """Create a fake shutil module with a configurable which() map.

    Args:
        which_map: Mapping from executable name to fake path or None.

    Returns:
        SimpleNamespace with a which() function.
    """

    def _which(name: str) -> str | None:
        return which_map.get(name)

    return types.SimpleNamespace(which=_which)


def test_yamllint_prefers_direct_binary_when_available(
    monkeypatch: pytest.MonkeyPatch,
    yamllint_tool: YamllintTool,
) -> None:
    """Prefer direct ``yamllint`` binary over ``uv run yamllint`` when present.

    This matches the Docker image setup where yamllint is installed
    system-wide, avoiding uv environment discrepancies between CI and local.
    """
    from lintro.tools import core as core_pkg

    fake_shutil = _make_fake_shutil(
        {
            "yamllint": "/usr/local/bin/yamllint",
            "uv": "/usr/local/bin/uv",
            "uvx": None,
        },
    )
    monkeypatch.setattr(core_pkg.tool_base, "shutil", fake_shutil)

    cmd = yamllint_tool._get_executable_command(tool_name="yamllint")
    assert cmd == ["yamllint"]


def test_yamllint_uses_uv_when_binary_missing_but_uv_available(
    monkeypatch: pytest.MonkeyPatch,
    yamllint_tool: YamllintTool,
) -> None:
    """Fall back to ``uv run yamllint`` when only uv is available on PATH."""
    from lintro.tools import core as core_pkg

    fake_shutil = _make_fake_shutil(
        {
            "yamllint": None,
            "uv": "/usr/local/bin/uv",
            "uvx": None,
        },
    )
    monkeypatch.setattr(core_pkg.tool_base, "shutil", fake_shutil)

    cmd = yamllint_tool._get_executable_command(tool_name="yamllint")
    assert cmd == ["uv", "run", "yamllint"]


def test_yamllint_falls_back_to_plain_name_when_no_helpers(
    monkeypatch: pytest.MonkeyPatch,
    yamllint_tool: YamllintTool,
) -> None:
    """Fall back gracefully to ``yamllint`` when nothing is on PATH."""
    from lintro.tools import core as core_pkg

    fake_shutil = _make_fake_shutil({"yamllint": None, "uv": None, "uvx": None})
    monkeypatch.setattr(core_pkg.tool_base, "shutil", fake_shutil)

    cmd = yamllint_tool._get_executable_command(tool_name="yamllint")
    assert cmd == ["yamllint"]
