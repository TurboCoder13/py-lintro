"""Tests for Lintro CLI."""

import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from lintro.cli import cli


class TestCLI(unittest.TestCase):
    """Test the CLI interface."""

    def setUp(self):
        """Set up the test environment."""
        self.runner = CliRunner()

    def test_version(self):
        """Test the --version option."""
        result = self.runner.invoke(cli, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("lintro, version", result.output)

    @patch("lintro.tools.AVAILABLE_TOOLS")
    def test_list_tools(self, mock_tools):
        """Test the list-tools command."""
        mock_tools.items.return_value = [
            ("black", MagicMock(name="black", description="Black formatter", can_fix=True)),
            ("flake8", MagicMock(name="flake8", description="Flake8 linter", can_fix=False)),
        ]
        
        result = self.runner.invoke(cli, ["list-tools"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("black", result.output)
        self.assertIn("flake8", result.output)
        self.assertIn("can fix", result.output)
        self.assertIn("check only", result.output)

    @patch("lintro.tools.CHECK_TOOLS")
    @patch("os.getcwd")
    def test_check_no_path(self, mock_getcwd, mock_tools):
        """Test the check command with no path argument."""
        mock_getcwd.return_value = "/test/path"
        mock_tool = MagicMock()
        mock_tool.check.return_value = (True, "No issues found")
        mock_tools.items.return_value = [("test-tool", mock_tool)]
        
        result = self.runner.invoke(cli, ["check"])
        
        self.assertEqual(result.exit_code, 0)
        mock_tool.check.assert_called_once_with(["/test/path"])
        self.assertIn("No issues found", result.output)

    @patch("lintro.tools.FIX_TOOLS")
    def test_fmt_with_path(self, mock_tools):
        """Test the fmt command with a path argument."""
        mock_tool = MagicMock()
        mock_tool.fix.return_value = (True, "Fixed issues")
        mock_tools.items.return_value = [("test-tool", mock_tool)]
        
        with self.runner.isolated_filesystem():
            with open("test_file.py", "w") as f:
                f.write("# Test file")
            
            result = self.runner.invoke(cli, ["fmt", "test_file.py"])
            
            self.assertEqual(result.exit_code, 0)
            mock_tool.fix.assert_called_once_with(["test_file.py"])
            self.assertIn("Fixed issues", result.output)

    @patch("lintro.tools.FIX_TOOLS")
    def test_fmt_with_specific_tools(self, mock_tools):
        """Test the fmt command with specific tools."""
        mock_black = MagicMock()
        mock_black.fix.return_value = (True, "Black fixed issues")
        mock_isort = MagicMock()
        mock_isort.fix.return_value = (True, "isort fixed issues")
        
        mock_tools.items.return_value = [
            ("black", mock_black),
            ("isort", mock_isort),
        ]
        
        with self.runner.isolated_filesystem():
            with open("test_file.py", "w") as f:
                f.write("# Test file")
            
            result = self.runner.invoke(cli, ["fmt", "--tools", "black", "test_file.py"])
            
            self.assertEqual(result.exit_code, 0)
            mock_black.fix.assert_called_once_with(["test_file.py"])
            mock_isort.fix.assert_not_called()


if __name__ == "__main__":
    unittest.main() 