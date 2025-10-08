"""Unit tests for BaseTool subprocess wrapper behaviors."""

from __future__ import annotations

import subprocess
from typing import Never

import pytest

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.tools.core.tool_base import BaseTool


class _DummyTool(BaseTool):
    name: str = "dummy"
    description: str = "dummy"
    can_fix: bool = False
    config: ToolConfig = ToolConfig(
        priority=1,
        conflicts_with=[],
        file_patterns=["*"],
        tool_type=ToolType.SECURITY,
    )

    def check(self, paths: list[str]) -> Never:  # type: ignore[override]
        raise NotImplementedError

    def fix(self, paths: list[str]) -> Never:  # type: ignore[override]
        raise NotImplementedError


@pytest.fixture()
def tool() -> _DummyTool:
    """Provide a dummy tool instance for subprocess wrapper tests.

    Returns:
        _DummyTool: Configured dummy tool instance.
    """
    return _DummyTool(name="dummy", description="dummy", can_fix=False)


def test_run_subprocess_file_not_found(tool: _DummyTool) -> None:
    """Raise FileNotFoundError when command is not found.

    Args:
        tool: Dummy tool instance used to invoke subprocess wrapper.
    """
    with pytest.raises(FileNotFoundError) as exc:
        tool._run_subprocess(["this-command-should-not-exist-xyz"])
    assert "Command not found:" in str(exc.value)


def test_run_subprocess_timeout(
    tool: _DummyTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise TimeoutExpired when subprocess exceeds timeout.

    Args:
        tool: Dummy tool instance.
        monkeypatch: Pytest monkeypatch to stub subprocess.
    """

    def _raise_timeout(*_a, **_k) -> Never:
        raise subprocess.TimeoutExpired(cmd=["echo"], timeout=0.01)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        tool._run_subprocess(["echo"])  # validated args; will raise timeout


def test_run_subprocess_called_process_error(
    tool: _DummyTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise CalledProcessError when subprocess fails with error.

    Args:
        tool: Dummy tool instance.
        monkeypatch: Pytest monkeypatch to stub subprocess.
    """

    def _raise_cpe(*_a, **_k) -> Never:
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["false"],
            output="oops",
            stderr="fail",
        )

    monkeypatch.setattr(subprocess, "run", _raise_cpe)
    with pytest.raises(subprocess.CalledProcessError):
        tool._run_subprocess(["false"])  # validated args; will raise CPE
