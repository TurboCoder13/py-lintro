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
from lintro.tools.prettier import PrettierTool
from lintro.tools.pydocstyle import PydocstyleTool
from lintro.tools.pylint import PylintTool


def test_tool_interface():
    """Test that all tools implement the Tool interface."""
    tools = [
        BlackTool(), 
        IsortTool(), 
        Flake8Tool(), 
        DarglintTool(), 
        HadolintTool(),
        PrettierTool(),
        PydocstyleTool(),
        PylintTool(),
    ]

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


@patch("subprocess.Popen")
def test_pydocstyle_check_success(mock_popen):
    """Test pydocstyle check when no docstring style issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("", "")
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = PydocstyleTool()
        success, output = tool.check(["test.py"])

    assert success is True
    assert output == "No docstring style issues found."
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_pydocstyle_check_failure(mock_popen):
    """Test pydocstyle check when docstring style issues are found."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (
        "test.py:10: D100 Missing docstring in public module", 
        ""
    )
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = PydocstyleTool()
        success, output = tool.check(["test.py"])

    assert success is False
    assert "D100" in output
    mock_popen.assert_called_once()


@patch("subprocess.Popen")
def test_pydocstyle_check_timeout(mock_popen):
    """Test pydocstyle check when a timeout occurs."""
    # Mock the process
    mock_process = MagicMock()
    mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="pydocstyle", timeout=10)
    mock_popen.return_value = mock_process

    # Mock os.path.isdir, os.path.isfile, and os.walk
    with patch("os.path.isdir", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.walk", return_value=[]):
        tool = PydocstyleTool()
        success, output = tool.check(["test.py"])

    assert success is False
    assert "timeout" in output.lower()
    mock_popen.assert_called_once()


def test_pydocstyle_fix():
    """Test that pydocstyle cannot fix issues."""
    tool = PydocstyleTool()
    success, output = tool.fix(["test.py"])

    assert success is False
    assert "cannot automatically fix" in output


@patch("subprocess.run")
def test_prettier_check_success(mock_run):
    """Test prettier check when no formatting issues are found."""
    mock_process = MagicMock()
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    tool = PrettierTool()
    success, output = tool.check(["test.js"])

    assert success is True
    assert output == "All files are formatted correctly."
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_prettier_check_failure(mock_run):
    """Test prettier check when formatting issues are found."""
    # Use CalledProcessError instead of Exception to match what subprocess.run raises
    from subprocess import CalledProcessError

    error = CalledProcessError(
        1,
        ["npx", "prettier", "--check"],
        output="[warn] test.js would be formatted",
        stderr="",
    )
    mock_run.side_effect = error

    tool = PrettierTool()
    success, output = tool.check(["test.js"])

    assert success is False
    assert "would be formatted" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_prettier_fix_success(mock_run):
    """Test prettier fix when formatting is successful."""
    mock_process = MagicMock()
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    tool = PrettierTool()
    success, output = tool.fix(["test.js"])

    assert success is True
    assert output == "All files formatted successfully."
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_prettier_fix_failure(mock_run):
    """Test prettier fix when formatting fails."""
    # Use CalledProcessError instead of Exception to match what subprocess.run raises
    from subprocess import CalledProcessError

    error = CalledProcessError(
        1,
        ["npx", "prettier", "--write"],
        output="Error: Unable to format file",
        stderr="",
    )
    mock_run.side_effect = error

    tool = PrettierTool()
    success, output = tool.fix(["test.js"])

    assert success is False
    assert "Error formatting files" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_pylint_check_success(mock_run):
    """Test pylint check when no issues are found."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    tool = PylintTool()
    success, output = tool.check(["test.py"])

    assert success is True
    assert "No issues found" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_pylint_check_failure(mock_run):
    """Test pylint check when issues are found."""
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stdout = (
        "test.py:10:0: C0111: Missing module docstring (missing-docstring)\n"
        "test.py:12:0: C0103: Variable name 'x' doesn't conform to snake_case naming style (invalid-name)"
    )
    mock_run.return_value = mock_process

    tool = PylintTool()
    success, output = tool.check(["test.py"])

    assert success is False
    assert "C0111" in output
    assert "C0103" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_pylint_check_with_rcfile(mock_run):
    """Test pylint check with custom rcfile."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    tool = PylintTool()
    tool.set_options(rcfile="custom_pylintrc")
    success, output = tool.check(["test.py"])

    assert success is True
    # Check that the rcfile was passed to pylint
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--rcfile" in cmd
    assert "custom_pylintrc" in cmd


def test_pylint_fix():
    """Test that pylint fix returns appropriate message."""
    tool = PylintTool()
    success, output = tool.fix(["test.py"])

    assert success is False
    assert "cannot automatically fix" in output
