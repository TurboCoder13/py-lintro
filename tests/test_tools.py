"""Tests for Lintro tools."""

import os
import subprocess
from unittest.mock import MagicMock, patch

from lintro.tools import Tool
from lintro.tools.black import BlackTool
from lintro.tools.darglint import DarglintTool
from lintro.tools.flake8 import Flake8Tool
from lintro.tools.hadolint import HadolintTool
from lintro.tools.isort import IsortTool


def test_tool_interface():
    """Test that all tools implement the Tool interface."""
    tools = [BlackTool(), IsortTool(), Flake8Tool(), DarglintTool(), HadolintTool()]

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


@patch("subprocess.Popen")
def test_darglint_check_success(mock_popen):
    """Test darglint check when no docstring issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("", "")
    mock_popen.return_value = mock_process

    # Mock os.path.isdir and os.path.isfile
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True):
        tool = DarglintTool()
        success, output = tool.check(["test.py"])

    assert success is True
    assert output == "No docstring issues found."
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_darglint_check_failure(mock_popen):
    """Test darglint check when docstring issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (
        "test.py:10:0: DAR101 Missing parameter(s) in Docstring: ['param']", 
        ""
    )
    mock_popen.return_value = mock_process

    # Mock os.path.isdir and os.path.isfile
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True):
        tool = DarglintTool()
        success, output = tool.check(["test.py"])

    assert success is False
    assert "DAR101" in output
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_darglint_check_timeout(mock_popen):
    """Test darglint check when a timeout occurs."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="darglint", timeout=10)
    mock_popen.return_value = mock_process

    # Mock os.path.isdir and os.path.isfile
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True):
        tool = DarglintTool()
        success, output = tool.check(["test.py"])

    assert success is False
    assert "timeout" in output.lower()
    mock_popen.assert_called_once()


def test_darglint_fix():
    """Test that darglint cannot fix issues."""
    tool = DarglintTool()
    success, output = tool.fix(["test.py"])

    assert success is False
    assert "cannot automatically fix" in output


@patch("subprocess.Popen")
def test_hadolint_check_success(mock_popen):
    """Test hadolint check when no Dockerfile issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("", "")
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = HadolintTool()
        success, output = tool.check(["Dockerfile"])

    assert success is True
    assert output == "No Dockerfile issues found."
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_hadolint_check_failure(mock_popen):
    """Test hadolint check when Dockerfile issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (
        "Dockerfile:3 DL3006 Always tag the version of an image explicitly", 
        ""
    )
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = HadolintTool()
        success, output = tool.check(["Dockerfile"])

    assert success is False
    assert "DL3006" in output
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_hadolint_check_timeout(mock_popen):
    """Test hadolint check when a timeout occurs."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="hadolint", timeout=10)
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = HadolintTool()
        success, output = tool.check(["Dockerfile"])

    assert success is False
    assert "timeout" in output.lower()
    mock_popen.assert_called_once()


def test_hadolint_fix():
    """Test that hadolint cannot fix issues."""
    tool = HadolintTool()
    success, output = tool.fix(["Dockerfile"])

    assert success is False
    assert "cannot automatically fix" in output
