"""Unit tests for yamllint executable resolution.

These tests ensure that BaseTool._get_executable_command chooses the
correct invocation strategy for yamllint so that Docker and local runs
behave consistently.

Note: Python bundled tools (yamllint, ruff, black, bandit) now use
``python -m <tool>`` to ensure they run in lintro's environment.
"""

from __future__ import annotations

import sys

import pytest
from assertpy import assert_that

from lintro.tools.implementations.yamllint_config import YamllintTool


@pytest.fixture()
def yamllint_tool() -> YamllintTool:
    """Provide a YamllintTool instance for executable resolution tests.

    Returns:
        YamllintTool: Configured YamllintTool instance.
    """
    return YamllintTool()


def test_yamllint_uses_python_module_invocation(
    yamllint_tool: YamllintTool,
) -> None:
    """Verify yamllint uses ``python -m yamllint`` for consistent execution.

    Python bundled tools use python -m invocation to ensure they run
    in lintro's environment, avoiding version conflicts with system tools.

    Args:
        yamllint_tool: YamllintTool instance for testing.
    """
    cmd = yamllint_tool._get_executable_command(tool_name="yamllint")
    assert_that(cmd).is_equal_to([sys.executable, "-m", "yamllint"])


def test_yamllint_falls_back_to_plain_name_when_no_python(
    monkeypatch: pytest.MonkeyPatch,
    yamllint_tool: YamllintTool,
) -> None:
    """Fall back to plain ``yamllint`` when Python executable is unavailable.

    This edge case handles environments where sys.executable is empty.

    Args:
        monkeypatch: Pytest fixture for patching attributes.
        yamllint_tool: YamllintTool instance for testing.
    """
    # Temporarily set sys.executable to empty string
    monkeypatch.setattr(sys, "executable", "")

    cmd = yamllint_tool._get_executable_command(tool_name="yamllint")
    assert_that(cmd).is_equal_to(["yamllint"])
