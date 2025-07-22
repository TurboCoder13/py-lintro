"""Tests for the tool utilities module.

This module contains tests for the tool utility functions in Lintro.
"""

import pytest

from lintro.utils.tool_utils import (
    parse_tool_list,
    parse_tool_options,
    should_exclude_path,
    get_table_columns,
    format_as_table,
    format_tool_output,
    walk_files_with_excludes,
)


@pytest.mark.utils
def test_parse_tool_list_basic():
    """Test parsing basic tool list."""
    result = parse_tool_list("ruff,yamllint")

    assert len(result) == 2
    assert "RUFF" in [tool.name for tool in result]
    assert "YAMLLINT" in [tool.name for tool in result]


@pytest.mark.utils
def test_parse_tool_list_empty():
    """Test parsing empty tool list."""
    result = parse_tool_list("")
    assert result == []


@pytest.mark.utils
def test_parse_tool_list_none():
    """Test parsing None tool list."""
    result = parse_tool_list(None)
    assert result == []


@pytest.mark.utils
def test_parse_tool_list_invalid_tool():
    """Test parsing invalid tool name."""
    with pytest.raises(ValueError, match="Unknown core"):
        parse_tool_list("invalid_tool")


@pytest.mark.utils
def test_parse_tool_options_basic():
    """Test parsing basic tool options."""
    options_str = "ruff:line-length=88,yamllint:max-line-length=120"
    result = parse_tool_options(options_str)

    assert "ruff" in result
    assert "yamllint" in result
    assert result["ruff"]["line-length"] == "88"
    assert result["yamllint"]["max-line-length"] == "120"


@pytest.mark.utils
def test_parse_tool_options_empty():
    """Test parsing empty tool options."""
    result = parse_tool_options("")
    assert result == {}


@pytest.mark.utils
def test_parse_tool_options_none():
    """Test parsing None tool options."""
    result = parse_tool_options(None)
    assert result == {}


@pytest.mark.utils
def test_parse_tool_options_invalid_format():
    """Test parsing invalid tool options format."""
    result = parse_tool_options("invalid:format:here")
    assert result == {}


@pytest.mark.utils
def test_should_exclude_path_basic():
    """Test basic path exclusion logic."""
    path = "/path/to/file.pyc"
    exclude_patterns = ["*.pyc"]

    result = should_exclude_path(path, exclude_patterns)
    assert result is True


@pytest.mark.utils
def test_should_exclude_path_not_excluded():
    """Test path not excluded."""
    path = "/path/to/file.py"
    exclude_patterns = ["*.pyc"]

    result = should_exclude_path(path, exclude_patterns)
    assert result is False


@pytest.mark.utils
def test_should_exclude_path_no_patterns():
    """Test path exclusion with no patterns."""
    path = "/path/to/file.py"
    exclude_patterns = []

    result = should_exclude_path(path, exclude_patterns)
    assert result is False


@pytest.mark.utils
def test_get_table_columns_basic():
    """Test getting table columns for basic issues."""
    issues = [
        {"file": "test.py", "line": "1", "message": "Error 1"},
        {"file": "test.py", "line": "5", "message": "Error 2"},
    ]

    columns, _ = get_table_columns(issues, "ruff")

    assert "File" in columns
    assert "Line" in columns
    assert "Message" in columns


@pytest.mark.utils
def test_get_table_columns_empty():
    """Test getting table columns for empty issues (should be empty)."""
    columns, _ = get_table_columns([], "ruff")
    assert columns == []


@pytest.mark.utils
def test_format_as_table_basic():
    """Test formatting issues as table."""
    issues = [
        {"file": "test.py", "line": "1", "message": "Error 1"},
        {"file": "test.py", "line": "5", "message": "Error 2"},
    ]

    result = format_as_table(issues, "ruff")

    assert isinstance(result, str)
    assert "test.py" in result
    assert "Error" in result


@pytest.mark.utils
def test_format_as_table_empty():
    """Test formatting empty issues as table."""
    result = format_as_table([], "ruff")

    assert isinstance(result, str)
    # Should return empty string for no issues, letting caller handle "No issues found"
    assert result == ""


@pytest.mark.utils
def test_format_tool_output_basic():
    """Test basic tool output formatting with non-parseable content."""
    output = "test output content"
    result = format_tool_output("unknown_tool", output)

    assert isinstance(result, str)
    # For unknown tools with unparseable content, should return the raw output
    assert result == output


@pytest.mark.utils
def test_format_tool_output_json():
    """Test tool output formatting with JSON format."""
    output = "test output content"
    result = format_tool_output("ruff", output, output_format="json")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.utils
def test_format_tool_output_csv():
    """Test tool output formatting with CSV format (using real ruff JSON output)."""
    output = '[{"filename": "test_samples/darglint_violations.py", "location": {"row": 1, "column": 1}, "end_location": {"row": 1, "column": 10}, "code": "F401", "message": "\'os\' imported but unused", "url": null, "fix": null}]'
    result = format_tool_output("ruff", output, output_format="csv")
    print("DEBUG: CSV result=\n", repr(result))
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.utils
def test_walk_files_with_excludes_basic(temp_dir):
    """Test walking files with basic excludes.

    Args:
        temp_dir (Path): Temporary directory fixture for test files.
    """
    # Create test files
    test_file = temp_dir / "test.py"
    test_file.write_text("test content")
    ignore_file = temp_dir / "ignore.pyc"
    ignore_file.write_text("ignore content")

    paths = [str(temp_dir)]
    file_patterns = ["*.py", "*.pyc"]
    exclude_patterns = ["*.pyc"]

    result = walk_files_with_excludes(paths, file_patterns, exclude_patterns)

    assert str(test_file) in result
    assert str(ignore_file) not in result


@pytest.mark.utils
def test_walk_files_with_excludes_venv(temp_dir):
    """Test walking files excludes venv directories.

    Args:
        temp_dir (Path): Temporary directory fixture for test files.
    """
    # Create venv-like structure
    venv_dir = temp_dir / ".venv"
    venv_dir.mkdir()
    venv_file = venv_dir / "test.py"
    venv_file.write_text("venv content")

    paths = [str(temp_dir)]
    file_patterns = ["*.py"]
    exclude_patterns = []

    result = walk_files_with_excludes(
        paths, file_patterns, exclude_patterns, include_venv=False
    )

    assert str(venv_file) not in result


@pytest.mark.utils
def test_walk_files_with_excludes_include_venv(temp_dir):
    """Test walking files includes venv when specified.

    Args:
        temp_dir (Path): Temporary directory fixture for test files.
    """
    # Create venv-like structure
    venv_dir = temp_dir / ".venv"
    venv_dir.mkdir()
    venv_file = venv_dir / "test.py"
    venv_file.write_text("venv content")

    paths = [str(temp_dir)]
    file_patterns = ["*.py"]
    exclude_patterns = []

    result = walk_files_with_excludes(
        paths, file_patterns, exclude_patterns, include_venv=True
    )

    assert str(venv_file) in result


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing.

    Yields:
        Path: Path to the temporary directory.
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
