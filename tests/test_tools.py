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
from lintro.tools.semgrep import SemgrepTool


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
        SemgrepTool(),
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


@patch("subprocess.run")
def test_semgrep_check_success(mock_run):
    """Test semgrep check when no issues are found."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = """
┌─────────────────┐
│ 0 Code Findings │
└─────────────────┘

┌──────────────┐
│ Scan Summary │
└──────────────┘

Ran 290 rules on 1 file: 0 findings.
"""
    mock_run.return_value = mock_process

    tool = SemgrepTool()
    success, output = tool.check(["test.py"])

    assert success is True
    assert output == "No issues found."
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_semgrep_check_failure(mock_run):
    """Test semgrep check when issues are found."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = """
┌─────────────────┐
│ 2 Code Findings │
└─────────────────┘

    test.py
   ❯❯❱ python.lang.security.audit.eval-detected
          Detected eval(). This is dangerous.

           21┆ result = eval(user_input)

┌──────────────┐
│ Scan Summary │
└──────────────┘

Ran 290 rules on 1 file: 2 findings.
"""
    mock_run.return_value = mock_process

    tool = SemgrepTool()
    success, output = tool.check(["test.py"])

    assert success is False
    assert "test.py" in output
    assert "python.lang.security.audit.eval-detected" in output
    assert "result = eval(user_input)" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_semgrep_check_with_config(mock_run):
    """Test semgrep check with custom configuration."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = """
┌─────────────────┐
│ 0 Code Findings │
└─────────────────┘

┌──────────────┐
│ Scan Summary │
└──────────────┘

Ran 290 rules on 1 file: 0 findings.
"""
    mock_run.return_value = mock_process

    tool = SemgrepTool()
    tool.set_options(config_option="p/python")
    success, output = tool.check(["test.py"])

    assert success is True
    # Check that the config was passed to semgrep
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--config" in cmd
    assert "p/python" in cmd


def test_semgrep_fix():
    """Test that semgrep fix returns appropriate message."""
    tool = SemgrepTool()
    success, output = tool.fix(["test.py"])

    assert success is False
    assert "cannot automatically fix" in output


@patch("subprocess.run")
def test_terraform_check_success(mock_run):
    """Test terraform check when no issues are found."""
    # Mock the format check process
    mock_fmt_process = MagicMock()
    mock_fmt_process.returncode = 0
    mock_fmt_process.stdout = ""
    
    # Mock the validate process
    mock_validate_process = MagicMock()
    mock_validate_process.returncode = 0
    mock_validate_process.stdout = """
{
  "format_version": "1.0",
  "valid": true,
  "error_count": 0,
  "warning_count": 0,
  "diagnostics": []
}
"""
    
    # Set up the mock to return different values for different commands
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "fmt" in cmd:
            return mock_fmt_process
        elif "validate" in cmd:
            return mock_validate_process
        return MagicMock()
    
    mock_run.side_effect = side_effect

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the check method
    success, output = tool.check(["test_dir"])

    # Verify the results
    assert success is True
    assert "No Terraform issues found" in output
    assert mock_run.call_count >= 2  # At least fmt and validate calls


@patch("subprocess.run")
def test_terraform_check_format_failure(mock_run):
    """Test terraform check when formatting issues are found."""
    # Mock the format check process
    mock_fmt_process = MagicMock()
    mock_fmt_process.returncode = 1
    mock_fmt_process.stdout = """
--- old/main.tf
+++ new/main.tf
@@ -1,3 +1,3 @@
 resource "aws_instance" "example" {
-  ami = "ami-12345678"
+  ami           = "ami-12345678"
 }
"""
    
    # Mock the validate process
    mock_validate_process = MagicMock()
    mock_validate_process.returncode = 0
    mock_validate_process.stdout = """
{
  "format_version": "1.0",
  "valid": true,
  "error_count": 0,
  "warning_count": 0,
  "diagnostics": []
}
"""
    
    # Set up the mock to return different values for different commands
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "fmt" in cmd:
            return mock_fmt_process
        elif "validate" in cmd:
            return mock_validate_process
        return MagicMock()
    
    mock_run.side_effect = side_effect

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the check method
    success, output = tool.check(["test_dir"])

    # Verify the results
    assert success is False
    assert "Formatting issues found" in output
    assert "main.tf" in output
    assert mock_run.call_count >= 2  # At least fmt and validate calls


@patch("subprocess.run")
def test_terraform_check_validate_failure(mock_run):
    """Test terraform check when validation issues are found."""
    # Mock the format check process
    mock_fmt_process = MagicMock()
    mock_fmt_process.returncode = 0
    mock_fmt_process.stdout = ""
    
    # Mock the validate process
    mock_validate_process = MagicMock()
    mock_validate_process.returncode = 0
    mock_validate_process.stdout = """
{
  "format_version": "1.0",
  "valid": false,
  "error_count": 1,
  "warning_count": 0,
  "diagnostics": [
    {
      "severity": "error",
      "summary": "Reference to undeclared resource",
      "detail": "A managed resource \"aws_security_group\" \"example\" has not been declared in the root module.",
      "range": {
        "filename": "main.tf",
        "start": {
          "line": 3,
          "column": 5,
          "byte": 74
        },
        "end": {
          "line": 3,
          "column": 34,
          "byte": 103
        }
      }
    }
  ]
}
"""
    
    # Set up the mock to return different values for different commands
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "fmt" in cmd:
            return mock_fmt_process
        elif "validate" in cmd:
            return mock_validate_process
        return MagicMock()
    
    mock_run.side_effect = side_effect

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the check method
    success, output = tool.check(["test_dir"])

    # Verify the results
    assert success is False
    assert "Validation issues found" in output
    assert "Reference to undeclared resource" in output
    assert mock_run.call_count >= 2  # At least fmt and validate calls


@patch("subprocess.run")
def test_terraform_fix_success(mock_run):
    """Test terraform fix when formatting is successful."""
    # Mock the format process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "main.tf\nvariables.tf"
    mock_run.return_value = mock_process

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the fix method
    success, output = tool.fix(["test_dir"])

    # Verify the results
    assert success is True
    assert "Formatted 2 Terraform files" in output
    assert "main.tf" in output
    assert "variables.tf" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_terraform_fix_no_changes(mock_run):
    """Test terraform fix when no formatting is needed."""
    # Mock the format process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = ""
    mock_run.return_value = mock_process

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the fix method
    success, output = tool.fix(["test_dir"])

    # Verify the results
    assert success is True
    assert "No Terraform files needed formatting" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_terraform_fix_failure(mock_run):
    """Test terraform fix when formatting fails."""
    # Mock the format process
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stderr = "Error formatting Terraform files"
    mock_run.return_value = mock_process

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Call the fix method
    success, output = tool.fix(["test_dir"])

    # Verify the results
    assert success is False
    assert "Error formatting Terraform files" in output
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_terraform_check_with_recursive_option(mock_run):
    """Test terraform check with recursive option."""
    # Mock the format check process
    mock_fmt_process = MagicMock()
    mock_fmt_process.returncode = 0
    mock_fmt_process.stdout = ""
    
    # Mock the validate process
    mock_validate_process = MagicMock()
    mock_validate_process.returncode = 0
    mock_validate_process.stdout = """
{
  "format_version": "1.0",
  "valid": true,
  "error_count": 0,
  "warning_count": 0,
  "diagnostics": []
}
"""
    
    # Set up the mock to return different values for different commands
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "fmt" in cmd:
            return mock_fmt_process
        elif "validate" in cmd:
            return mock_validate_process
        return MagicMock()
    
    mock_run.side_effect = side_effect

    # Create a TerraformTool instance
    from lintro.tools.terraform import TerraformTool
    tool = TerraformTool()
    
    # Set the recursive option to False
    tool.set_options(recursive=False)
    
    # Call the check method
    success, output = tool.check(["test_dir"])

    # Verify the results
    assert success is True
    assert "No Terraform issues found" in output
    
    # Check that the recursive flag was not passed to terraform fmt
    fmt_cmd = None
    for call in mock_run.call_args_list:
        if "fmt" in call[0][0]:
            fmt_cmd = call[0][0]
            break
    
    assert fmt_cmd is not None
    assert "-recursive" not in fmt_cmd
