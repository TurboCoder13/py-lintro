"""Tests for Lintro tools."""

from unittest.mock import MagicMock, patch

from lintro.tools import Tool
from lintro.tools.black import BlackTool
from lintro.tools.flake8 import Flake8Tool
from lintro.tools.isort import IsortTool


def test_tool_interface():
    """Test that all tools implement the Tool interface."""
    tools = [BlackTool(), IsortTool(), Flake8Tool()]

    for tool in tools:
        assert isinstance(tool, Tool)
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "can_fix")
        assert callable(tool.check)
        assert callable(tool.fix)


@patch("subprocess.run")
def test_black_check_success(mock_run):
    """Test Black check when no formatting is needed."""
    mock_process = MagicMock()
    mock_process.stdout = "All files would be left unchanged."
    mock_run.return_value = mock_process

    tool = BlackTool()
    success, output = tool.check(["test.py"])

    assert success is True
    assert output == "All files would be left unchanged."
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_black_check_failure(mock_run):
    """Test Black check when formatting is needed."""
    # Use CalledProcessError instead of Exception to match what subprocess.run raises
    from subprocess import CalledProcessError

    error = CalledProcessError(
        1,
        ["black", "--check"],
        output="Would reformat test.py",
        stderr="",
    )
    mock_run.side_effect = error

    tool = BlackTool()
    success, output = tool.check(["test.py"])

    assert success is False
    assert "Would reformat test.py" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_isort_check_success(mock_run):
    """Test isort check when no sorting is needed."""
    mock_process = MagicMock()
    mock_process.stdout = "All imports are correctly sorted."
    mock_run.return_value = mock_process

    tool = IsortTool()
    success, output = tool.check(["test.py"])

    assert success is True
    assert output == "All imports are correctly sorted."
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_flake8_check_success(mock_run):
    """Test flake8 check when no issues are found."""
    mock_process = MagicMock()
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    tool = Flake8Tool()
    success, output = tool.check(["test.py"])

    assert success is True
    assert output == "No style issues found."
    mock_run.assert_called_once()


def test_flake8_fix():
    """Test that flake8 cannot fix issues."""
    tool = Flake8Tool()
    success, output = tool.fix(["test.py"])

    assert success is False
    assert "cannot automatically fix" in output
