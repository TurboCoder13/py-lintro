from __future__ import annotations

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


@pytest.mark.parametrize(
    "cmd",
    [
        ["echo", "hello"],
        ["python", "-c", "print('ok')"],
        ["git", "status"],
    ],
)
def test_validator_allows_safe_commands(tool: _DummyTool, cmd: list[str]) -> None:
    tool._validate_subprocess_command(cmd=cmd)


@pytest.mark.parametrize(
    "cmd",
    [
        [],
        ["echo", "hello; rm -rf /"],
        ["sh", "-c", "echo hi && whoami"],
        ["git", "log", "HEAD|cat"],
        ["git", "log", "`whoami`"],
        ["git", "log", "$(whoami)"],
        ["echo", "hi\nthere"],
    ],
)
def test_validator_rejects_unsafe_commands(tool: _DummyTool, cmd: list[str]) -> None:
    with pytest.raises(ValueError):
        tool._validate_subprocess_command(cmd=cmd)
