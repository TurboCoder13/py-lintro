"""Tests for Lintro tools."""

import unittest
from unittest.mock import patch, MagicMock

from lintro.tools import Tool
from lintro.tools.black import BlackTool
from lintro.tools.isort import IsortTool
from lintro.tools.flake8 import Flake8Tool


class TestTools(unittest.TestCase):
    """Test the tool implementations."""

    def test_tool_interface(self):
        """Test that all tools implement the Tool interface."""
        tools = [BlackTool(), IsortTool(), Flake8Tool()]
        
        for tool in tools:
            self.assertIsInstance(tool, Tool)
            self.assertTrue(hasattr(tool, "name"))
            self.assertTrue(hasattr(tool, "description"))
            self.assertTrue(hasattr(tool, "can_fix"))
            self.assertTrue(callable(tool.check))
            self.assertTrue(callable(tool.fix))

    @patch("subprocess.run")
    def test_black_check_success(self, mock_run):
        """Test Black check when no formatting is needed."""
        mock_process = MagicMock()
        mock_process.stdout = "All files would be left unchanged."
        mock_run.return_value = mock_process
        
        tool = BlackTool()
        success, output = tool.check(["test.py"])
        
        self.assertTrue(success)
        self.assertEqual(output, "All files would be left unchanged.")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_black_check_failure(self, mock_run):
        """Test Black check when formatting is needed."""
        mock_run.side_effect = Exception("Would reformat test.py")
        
        tool = BlackTool()
        success, output = tool.check(["test.py"])
        
        self.assertFalse(success)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_isort_check_success(self, mock_run):
        """Test isort check when no sorting is needed."""
        mock_process = MagicMock()
        mock_process.stdout = "All imports are correctly sorted."
        mock_run.return_value = mock_process
        
        tool = IsortTool()
        success, output = tool.check(["test.py"])
        
        self.assertTrue(success)
        self.assertEqual(output, "All imports are correctly sorted.")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_flake8_check_success(self, mock_run):
        """Test flake8 check when no issues are found."""
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        tool = Flake8Tool()
        success, output = tool.check(["test.py"])
        
        self.assertTrue(success)
        self.assertEqual(output, "No style issues found.")
        mock_run.assert_called_once()

    def test_flake8_fix(self):
        """Test that flake8 cannot fix issues."""
        tool = Flake8Tool()
        success, output = tool.fix(["test.py"])
        
        self.assertFalse(success)
        self.assertTrue("cannot automatically fix" in output)


if __name__ == "__main__":
    unittest.main() 