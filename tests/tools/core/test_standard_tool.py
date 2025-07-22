"""
test_standard_tool.py

Tests for StandardTool base class.
"""
import pytest
import subprocess
from lintro.tools.core.standard_tool import StandardTool

def test_run_success(tmp_path):
    tool = StandardTool(name="echo")
    result = tool.run(command=["echo", "hello"], cwd=None)
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert tool.is_success(result) is True

def test_run_timeout():
    tool = StandardTool(name="sleep", timeout=1)
    with pytest.raises(RuntimeError):
        tool.run(command=["python3", "-c", "import time; time.sleep(2)"])

def test_is_success():
    tool = StandardTool(name="false")
    result = tool.run(command=["python3", "-c", "import sys; sys.exit(1)"])
    assert tool.is_success(result) is False

def test_validate_options_valid():
    tool = StandardTool(name="dummy", options={"foo": 1, "bar": "baz", "qux": True})
    tool.validate_options()

def test_validate_options_invalid():
    tool = StandardTool(name="dummy", options={"foo": object()})
    with pytest.raises(ValueError):
        tool.validate_options() 