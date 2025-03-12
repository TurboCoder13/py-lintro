"""Tests for mypy integration."""

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from lintro.cli import cli
from lintro.tools.mypy import MypyTool


def test_mypy_tool_initialization() -> None:
    """Test that the mypy tool can be initialized."""
    tool = MypyTool()
    assert tool.name == "mypy"
    assert tool.description == "Static type checker for Python"
    assert tool.can_fix is False


def test_mypy_check_valid_file() -> None:
    """Test that mypy can check a valid file."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(
            b"""
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
"""
        )
        f.flush()
        
        tool = MypyTool()
        success, output = tool.check([f.name])
        
        # Clean up
        os.unlink(f.name)
        
        assert success is True
        assert "No type issues found" in output


def test_mypy_check_invalid_file() -> None:
    """Test that mypy can detect type errors."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(
            b"""
def greet(name: str) -> int:  # Return type is int but function returns str
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
"""
        )
        f.flush()
        
        tool = MypyTool()
        success, output = tool.check([f.name])
        
        # Clean up
        os.unlink(f.name)
        
        assert success is False
        assert "Incompatible return value type" in output or "Return value expected to be" in output


def test_mypy_cli_integration() -> None:
    """Test that mypy can be run through the CLI."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a Python file with a type error
        file_path = Path(tmpdir) / "test.py"
        with open(file_path, "w") as f:
            f.write(
                """
def greet(name: str) -> int:  # Return type is int but function returns str
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
"""
            )
        
        # Run the CLI with mypy
        result = runner.invoke(cli, ["check", "--tools", "mypy", str(file_path)])
        
        assert result.exit_code == 1  # Should fail due to type error
        assert "mypy" in result.output
        assert "Incompatible return value type" in result.output or "Return value expected to be" in result.output


def test_mypy_fix_not_supported() -> None:
    """Test that mypy fix is not supported."""
    tool = MypyTool()
    success, output = tool.fix(["dummy.py"])
    
    assert success is False
    assert "cannot automatically fix issues" in output


def test_mypy_options() -> None:
    """Test that mypy options can be set."""
    tool = MypyTool()
    tool.set_options(
        config_file="mypy.ini",
        python_version="3.8",
        disallow_untyped_defs=True,
        disallow_incomplete_defs=True,
    )
    
    assert tool.config_file == "mypy.ini"
    assert tool.python_version == "3.8"
    assert tool.disallow_untyped_defs is True
    assert tool.disallow_incomplete_defs is True 