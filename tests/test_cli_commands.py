"""Tests for Lintro CLI commands."""

import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from lintro.cli import cli, parse_tool_list


def test_parse_tool_list():
    """Test parsing a comma-separated list of tool names."""
    assert parse_tool_list(None) == []
    assert parse_tool_list("") == []
    assert parse_tool_list("black") == ["black"]
    assert parse_tool_list("black,isort") == ["black", "isort"]
    assert parse_tool_list("black, isort, flake8") == ["black", "isort", "flake8"]
    assert parse_tool_list(" black , isort , flake8 ") == ["black", "isort", "flake8"]


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version(runner):
    """Test the --version option."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


@patch("lintro.cli.AVAILABLE_TOOLS")
def test_list_tools_command(mock_tools, runner):
    """Test the list-tools command."""
    # Create mock tools
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.description = "Black formatter"
    mock_black.can_fix = True
    
    mock_flake8 = MagicMock()
    mock_flake8.name = "flake8"
    mock_flake8.description = "Flake8 linter"
    mock_flake8.can_fix = False
    
    # Set up the mock to return our mock tools
    mock_tools.items.return_value = [
        ("black", mock_black),
        ("flake8", mock_flake8),
    ]
    
    # Run the command
    result = runner.invoke(cli, ["list-tools"])
    
    # Check the result
    assert result.exit_code == 0
    assert "black" in result.output
    assert "flake8" in result.output 