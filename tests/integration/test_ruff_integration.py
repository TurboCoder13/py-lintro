"""Integration tests for Ruff tool."""

import pytest
import tempfile
import os

from lintro.tools.implementations.tool_ruff import RuffTool
from lintro.models.core.tool_result import ToolResult


@pytest.fixture
def ruff_tool():
    """Create a RuffTool instance for testing.

    Returns:
        RuffTool: A configured RuffTool instance.
    """
    return RuffTool()


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file with ruff violations.

    Yields:
        str: Path to the temporary Python file with violations.
    """
    content = '''"""Test file with ruff violations."""

import sys,os
import json
from pathlib    import Path

def hello(name:str='World'):
    print(f'Hello, {name}!')
    unused_var = 42

if __name__=='__main__':
    hello()
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def temp_clean_python_file():
    """Create a temporary Python file without violations.

    Yields:
        str: Path to the temporary clean Python file.
    """
    content = '''"""Clean Python file."""


def hello(name: str = "World") -> None:
    """Say hello to someone.
    
    Args:
        name: The name to greet
    """
    print(f"Hello, {name}!")


if __name__ == "__main__":
    hello()
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name

    # Cleanup
    os.unlink(f.name)


class TestRuffTool:
    """Test cases for RuffTool."""

    def test_tool_initialization(self, ruff_tool):
        """Test that RuffTool initializes correctly.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert ruff_tool.name == "ruff"
        assert ruff_tool.can_fix is True
        assert "*.py" in ruff_tool.config.file_patterns
        assert "*.pyi" in ruff_tool.config.file_patterns

    def test_tool_priority(self, ruff_tool):
        """Test that RuffTool has high priority.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert ruff_tool.config.priority == 85

    def test_check_with_violations(self, ruff_tool, temp_python_file):
        """Test checking a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            temp_python_file: Temporary Python file with violations.
        """
        result = ruff_tool.check([temp_python_file])

        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        assert result.success is False  # Should find issues
        assert result.issues_count > 0
        assert result.output != "No issues found."

    def test_check_clean_file(self, ruff_tool, temp_clean_python_file):
        """Test checking a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            temp_clean_python_file: Temporary clean Python file.
        """
        result = ruff_tool.check([temp_clean_python_file])

        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        assert result.success is True
        assert result.issues_count == 0

    def test_check_nonexistent_file(self, ruff_tool):
        """Test checking a nonexistent file.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(FileNotFoundError):
            ruff_tool.check(["/nonexistent/file.py"])

    def test_check_empty_paths(self, ruff_tool):
        """Test checking with empty paths.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        result = ruff_tool.check([])

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == "No files to check."
        assert result.issues_count == 0

    def test_fix_with_violations(self, ruff_tool, temp_python_file):
        """Test fixing a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            temp_python_file: Temporary Python file with violations.
        """
        result = ruff_tool.fix([temp_python_file])

        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        # After fixing, the file should be improved
        assert result.output != "No fixes applied."

    def test_set_options_valid(self, ruff_tool):
        """Test setting valid options.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(
            select=["E", "F"],
            ignore=["E501"],
            line_length=88,
            target_version="py39",
            unsafe_fixes=True,
            format=False,
        )

        assert ruff_tool.options["select"] == ["E", "F"]
        assert ruff_tool.options["ignore"] == ["E501"]
        assert ruff_tool.options["line_length"] == 88
        assert ruff_tool.options["target_version"] == "py39"
        assert ruff_tool.options["unsafe_fixes"] is True
        assert ruff_tool.options["format"] is False

    def test_set_options_invalid_select(self, ruff_tool):
        """Test setting invalid select option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="select must be a list"):
            ruff_tool.set_options(select="E,F")

    def test_set_options_invalid_line_length(self, ruff_tool):
        """Test setting invalid line length.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="line_length must be an integer"):
            ruff_tool.set_options(line_length="88")

        with pytest.raises(ValueError, match="line_length must be positive"):
            ruff_tool.set_options(line_length=-1)

    def test_build_check_command_basic(self, ruff_tool):
        """Test building basic check command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        assert cmd[0] == "ruff"
        assert cmd[1] == "check"
        assert "--output-format" in cmd
        assert "json" in cmd
        assert "test.py" in cmd

    def test_build_check_command_with_fix(self, ruff_tool):
        """Test building check command with fix option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)

        assert "--fix" in cmd

    def test_build_check_command_with_options(self, ruff_tool):
        """Test building check command with various options.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(
            select=["E", "F"],
            ignore=["E501"],
            line_length=88,
        )

        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        assert "--select" in cmd
        assert "E,F" in cmd
        assert "--ignore" in cmd
        assert "E501" in cmd
        assert "--line-length" in cmd
        assert "88" in cmd

    def test_build_format_command_basic(self, ruff_tool):
        """Test building basic format command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files)

        assert cmd[0] == "ruff"
        assert cmd[1] == "format"
        assert "test.py" in cmd

    def test_build_format_command_check_only(self, ruff_tool):
        """Test building format command in check-only mode.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files, check_only=True)

        assert "--check" in cmd
