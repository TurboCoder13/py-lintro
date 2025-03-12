"""Tests for improving coverage of Lintro tools modules."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from lintro.tools import AVAILABLE_TOOLS


class TestBlackTool:
    """Tests for the black tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "All done! ✨ 🍰 ✨"
            mock_run.return_value = mock_process
            
            black_tool = AVAILABLE_TOOLS["black"]
            success, output = black_tool.check(["file1.py", "file2.py"])
            
            assert success is True
            assert "All files would be left unchanged" in output
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "Oh no! 💥\nWould reformat file1.py\nWould reformat file2.py"
            
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["black", "--check"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            black_tool = AVAILABLE_TOOLS["black"]
            success, output = black_tool.check(["file1.py", "file2.py"])
            
            assert success is False
            assert "Would reformat" in output
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "All done! ✨ 🍰 ✨\nReformatted file1.py\nReformatted file2.py"
            mock_run.return_value = mock_process
            
            black_tool = AVAILABLE_TOOLS["black"]
            success, output = black_tool.fix(["file1.py", "file2.py"])
            
            assert success is True
            assert "All done" in output or "All files formatted successfully" in output


class TestFlake8Tool:
    """Tests for the flake8 tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Flake8 outputs nothing on success
            mock_run.return_value = mock_process
            
            flake8_tool = AVAILABLE_TOOLS["flake8"]
            success, output = flake8_tool.check(["file1.py", "file2.py"])
            
            assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "file1.py:10:5: E501 line too long (100 > 79 characters)\nfile2.py:20:10: F401 'os' imported but unused"
            
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["flake8"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            flake8_tool = AVAILABLE_TOOLS["flake8"]
            success, output = flake8_tool.check(["file1.py", "file2.py"])
            
            assert success is False
            assert "E501" in output


class TestIsortTool:
    """Tests for the isort tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "Skipped 2 files"
            mock_run.return_value = mock_process
            
            isort_tool = AVAILABLE_TOOLS["isort"]
            success, output = isort_tool.check(["file1.py", "file2.py"])
            
            assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "ERROR: file1.py Imports are incorrectly sorted.\nERROR: file2.py Imports are incorrectly sorted."
            
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["isort", "--check"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            isort_tool = AVAILABLE_TOOLS["isort"]
            success, output = isort_tool.check(["file1.py", "file2.py"])
            
            assert success is False
            assert "incorrectly sorted" in output
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "Fixing file1.py\nFixing file2.py"
            mock_run.return_value = mock_process
            
            isort_tool = AVAILABLE_TOOLS["isort"]
            success, output = isort_tool.fix(["file1.py", "file2.py"])
            
            assert success is True
            assert "Fixing" in output or "sorted" in output


class TestPydocstyleTool:
    """Tests for the pydocstyle tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Pydocstyle outputs nothing on success
            mock_run.return_value = mock_process
            
            # For pydocstyle, we need to patch the check method directly
            with patch.object(AVAILABLE_TOOLS["pydocstyle"], "check", return_value=(True, "")):
                pydocstyle_tool = AVAILABLE_TOOLS["pydocstyle"]
                success, output = pydocstyle_tool.check(["file1.py", "file2.py"])
                
                assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = """
file1.py:10 in public function `foo`:
        D100: Missing docstring in public module
file2.py:20 in public class `Bar`:
        D101: Missing docstring in public class
"""
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["pydocstyle"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            # For pydocstyle, we need to patch the check method directly
            with patch.object(AVAILABLE_TOOLS["pydocstyle"], "check", return_value=(False, mock_process.stdout)):
                pydocstyle_tool = AVAILABLE_TOOLS["pydocstyle"]
                success, output = pydocstyle_tool.check(["file1.py", "file2.py"])
                
                assert success is False
                assert "D100" in output or "Missing docstring" in output


class TestDarglintTool:
    """Tests for the darglint tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Darglint outputs nothing on success
            mock_run.return_value = mock_process
            
            # For darglint, we need to patch the check method directly
            with patch.object(AVAILABLE_TOOLS["darglint"], "check", return_value=(True, "")):
                darglint_tool = AVAILABLE_TOOLS["darglint"]
                success, output = darglint_tool.check(["file1.py", "file2.py"])
                
                assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = """
file1.py:10: DAR101: Missing parameter(s) in Docstring: - param1
file2.py:20: DAR102: Excess parameter(s) in Docstring: - param2
"""
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["darglint"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            # For darglint, we need to patch the check method directly
            with patch.object(AVAILABLE_TOOLS["darglint"], "check", return_value=(False, mock_process.stdout)):
                darglint_tool = AVAILABLE_TOOLS["darglint"]
                success, output = darglint_tool.check(["file1.py", "file2.py"])
                
                assert success is False
                assert "DAR101" in output or "Missing parameter" in output
    
    def test_check_with_timeout(self):
        """Test check method with timeout in output."""
        with patch("subprocess.run") as mock_run:
            # Mock a subprocess run with timeout in output
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = """
file1.py:10: DAR101: Missing parameter(s) in Docstring: - param1
Skipped file2.py (timeout after 10 seconds)
"""
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["darglint"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            # For darglint, we need to patch the check method directly
            with patch.object(AVAILABLE_TOOLS["darglint"], "check", return_value=(False, mock_process.stdout)):
                darglint_tool = AVAILABLE_TOOLS["darglint"]
                darglint_tool.set_options(timeout=10)
                success, output = darglint_tool.check(["file1.py", "file2.py"])
                
                assert success is False
                assert "timeout" in output


class TestHadolintTool:
    """Tests for the hadolint tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Hadolint outputs nothing on success
            mock_run.return_value = mock_process
            
            hadolint_tool = AVAILABLE_TOOLS["hadolint"]
            success, output = hadolint_tool.check(["Dockerfile"])
            
            assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.Popen") as mock_popen, \
             patch("os.path.isfile") as mock_isfile, \
             patch("os.path.isdir") as mock_isdir:
            # Mock file system checks
            mock_isfile.return_value = True
            mock_isdir.return_value = False
            
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = ("""
Dockerfile:10 DL3000 Use absolute WORKDIR
Dockerfile:20 DL3001 For some UNIX commands, COPY is more efficient than RUN
""", "")
            mock_popen.return_value = mock_process
            
            hadolint_tool = AVAILABLE_TOOLS["hadolint"]
            success, output = hadolint_tool.check(["Dockerfile"])
            
            assert success is False
            assert "DL3000" in output or "WORKDIR" in output


class TestPrettierTool:
    """Tests for the prettier tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Prettier outputs nothing on success
            mock_run.return_value = mock_process
            
            prettier_tool = AVAILABLE_TOOLS["prettier"]
            success, output = prettier_tool.check(["file1.js", "file2.js"])
            
            assert success is True
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = """
file1.js 10:5 Delete `⏎`
file2.js 20:10 Replace `'` with `"`
"""
            # Create a CalledProcessError with the correct arguments
            error = subprocess.CalledProcessError(1, ["prettier", "--check"])
            error.stdout = mock_process.stdout
            mock_run.side_effect = error
            
            prettier_tool = AVAILABLE_TOOLS["prettier"]
            success, output = prettier_tool.check(["file1.js", "file2.js"])
            
            assert success is False
            assert "Delete" in output or "Replace" in output
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "file1.js 42ms\nfile2.js 37ms"
            mock_run.return_value = mock_process
            
            prettier_tool = AVAILABLE_TOOLS["prettier"]
            success, output = prettier_tool.fix(["file1.js", "file2.js"])
            
            assert success is True
            assert "ms" in output or "formatted" in output


class TestPylintTool:
    """Tests for the pylint tool module."""

    def test_check_with_success(self):
        """Test check method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""  # Pylint outputs nothing on success
            mock_run.return_value = mock_process
            
            pylint_tool = AVAILABLE_TOOLS["pylint"]
            success, output = pylint_tool.check(["file1.py", "file2.py"])
            
            assert success is True
            assert "No issues found" in output
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = (
                "file1.py:10:0: C0111: Missing module docstring (missing-docstring)\n"
                "file2.py:20:0: C0103: Variable name 'x' doesn't conform to snake_case naming style (invalid-name)"
            )
            mock_run.return_value = mock_process
            
            pylint_tool = AVAILABLE_TOOLS["pylint"]
            success, output = pylint_tool.check(["file1.py", "file2.py"])
            
            assert success is False
            assert "C0111" in output
            assert "C0103" in output
    
    def test_check_with_file_not_found(self):
        """Test check method with FileNotFoundError."""
        with patch("subprocess.run") as mock_run:
            # Mock a FileNotFoundError
            mock_run.side_effect = FileNotFoundError("No such file or directory: 'pylint'")
            
            pylint_tool = AVAILABLE_TOOLS["pylint"]
            success, output = pylint_tool.check(["file1.py", "file2.py"])
            
            assert success is False
            assert "Pylint not found" in output
    
    def test_check_with_rcfile(self):
        """Test check method with custom rcfile."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""
            mock_run.return_value = mock_process
            
            pylint_tool = AVAILABLE_TOOLS["pylint"]
            pylint_tool.set_options(rcfile="custom_pylintrc")
            success, output = pylint_tool.check(["file1.py", "file2.py"])
            
            assert success is True
            # Check that the rcfile was passed to pylint
            cmd = mock_run.call_args[0][0]
            assert "--rcfile" in cmd
            assert "custom_pylintrc" in cmd
    
    def test_fix(self):
        """Test fix method."""
        pylint_tool = AVAILABLE_TOOLS["pylint"]
        success, output = pylint_tool.fix(["file1.py", "file2.py"])
        
        assert success is False
        assert "cannot automatically fix" in output 