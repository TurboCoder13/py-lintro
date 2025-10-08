from __future__ import annotations

import subprocess

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

    def check(self, paths: list[str]):  # type: ignore[override]
        raise NotImplementedError

    def fix(self, paths: list[str]):  # type: ignore[override]
        raise NotImplementedError


@pytest.fixture()
def tool() -> _DummyTool:
    return _DummyTool(name="dummy", description="dummy", can_fix=False)


def test_run_subprocess_file_not_found(tool: _DummyTool) -> None:
    with pytest.raises(FileNotFoundError) as exc:
        tool._run_subprocess(["this-command-should-not-exist-xyz"])
    assert "Command not found:" in str(exc.value)


def test_run_subprocess_timeout(
    tool: _DummyTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["echo"], timeout=0.01)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        tool._run_subprocess(["echo"])  # validated args; will raise timeout
