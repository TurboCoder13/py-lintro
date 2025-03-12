"""Tests for improving coverage of Lintro tools modules."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from lintro.tools import (
    black,
    darglint,
    flake8,
    hadolint,
    isort,
    prettier,
    pydocstyle,
)


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
            
            result = black.check(["file1.py", "file2.py"])
            
            assert result.success is True
            assert "All done" in result.output
            assert result.issues_count == 0
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "Oh no! 💥\nWould reformat file1.py\nWould reformat file2.py"
            mock_run.return_value = mock_process
            
            result = black.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "Would reformat" in result.output
            assert result.issues_count == 2
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "All done! ✨ 🍰 ✨\nReformatted file1.py\nReformatted file2.py"
            mock_run.return_value = mock_process
            
            result = black.fmt(["file1.py", "file2.py"])
            
            assert result.success is True
            assert "Reformatted" in result.output
            assert result.issues_count == 2


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
            
            result = flake8.check(["file1.py", "file2.py"])
            
            assert result.success is True
            assert result.issues_count == 0
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "file1.py:10:5: E501 line too long (100 > 79 characters)\nfile2.py:20:10: F401 'os' imported but unused"
            mock_run.return_value = mock_process
            
            result = flake8.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "E501" in result.output
            assert "F401" in result.output
            assert result.issues_count == 2


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
            
            result = isort.check(["file1.py", "file2.py"])
            
            assert result.success is True
            assert "Skipped" in result.output
            assert result.issues_count == 0
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = "ERROR: file1.py Imports are incorrectly sorted.\nERROR: file2.py Imports are incorrectly sorted."
            mock_run.return_value = mock_process
            
            result = isort.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "incorrectly sorted" in result.output
            assert result.issues_count == 2
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "Fixing file1.py\nFixing file2.py"
            mock_run.return_value = mock_process
            
            result = isort.fmt(["file1.py", "file2.py"])
            
            assert result.success is True
            assert "Fixing" in result.output
            assert result.issues_count == 2


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
            
            result = pydocstyle.check(["file1.py", "file2.py"])
            
            assert result.success is True
            assert result.issues_count == 0
    
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
            mock_run.return_value = mock_process
            
            result = pydocstyle.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "D100" in result.output
            assert "D101" in result.output
            assert result.issues_count == 2


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
            
            result = darglint.check(["file1.py", "file2.py"])
            
            assert result.success is True
            assert result.issues_count == 0
    
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
            mock_run.return_value = mock_process
            
            result = darglint.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "DAR101" in result.output
            assert "DAR102" in result.output
            assert result.issues_count == 2
    
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
            mock_run.return_value = mock_process
            
            result = darglint.check(["file1.py", "file2.py"])
            
            assert result.success is False
            assert "DAR101" in result.output
            assert "timeout" in result.output
            assert result.issues_count == 2  # One error + one timeout


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
            
            result = hadolint.check(["Dockerfile"])
            
            assert result.success is True
            assert result.issues_count == 0
    
    def test_check_with_failure(self):
        """Test check method with failure result."""
        with patch("subprocess.run") as mock_run:
            # Mock a failed subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stdout = """
Dockerfile:10 DL3000 Use absolute WORKDIR
Dockerfile:20 DL3001 For some UNIX commands, COPY is more efficient than RUN
"""
            mock_run.return_value = mock_process
            
            result = hadolint.check(["Dockerfile"])
            
            assert result.success is False
            assert "DL3000" in result.output
            assert "DL3001" in result.output
            assert result.issues_count == 2


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
            
            result = prettier.check(["file1.js", "file2.js"])
            
            assert result.success is True
            assert result.issues_count == 0
    
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
            mock_run.return_value = mock_process
            
            result = prettier.check(["file1.js", "file2.js"])
            
            assert result.success is False
            assert "Delete" in result.output
            assert "Replace" in result.output
            assert result.issues_count == 2
    
    def test_fmt_with_success(self):
        """Test fmt method with successful result."""
        with patch("subprocess.run") as mock_run:
            # Mock a successful subprocess run
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "file1.js 42ms\nfile2.js 37ms"
            mock_run.return_value = mock_process
            
            result = prettier.fmt(["file1.js", "file2.js"])
            
            assert result.success is True
            assert "file1.js" in result.output
            assert "file2.js" in result.output
            assert result.issues_count == 2 