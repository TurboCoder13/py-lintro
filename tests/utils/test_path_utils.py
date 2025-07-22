"""Tests for the path utilities module."""

import pytest
from unittest.mock import patch

from lintro.utils.path_utils import normalize_file_path_for_display


@pytest.mark.utils
def test_normalize_file_path_for_display_absolute():
    """Test normalizing an absolute path."""
    with patch("os.getcwd", return_value="/project/root"):
        with patch("os.path.abspath", return_value="/project/root/src/file.py"):
            with patch("os.path.relpath", return_value="src/file.py"):
                result = normalize_file_path_for_display("/project/root/src/file.py")

    assert result == "./src/file.py"


@pytest.mark.utils
def test_normalize_file_path_for_display_relative():
    """Test normalizing a relative path."""
    with patch("os.getcwd", return_value="/project/root"):
        with patch("os.path.abspath", return_value="/project/root/src/file.py"):
            with patch("os.path.relpath", return_value="src/file.py"):
                result = normalize_file_path_for_display("src/file.py")

    assert result == "./src/file.py"


@pytest.mark.utils
def test_normalize_file_path_for_display_current_dir():
    """Test normalizing a file in current directory."""
    with patch("os.getcwd", return_value="/project/root"):
        with patch("os.path.abspath", return_value="/project/root/file.py"):
            with patch("os.path.relpath", return_value="file.py"):
                result = normalize_file_path_for_display("file.py")

    assert result == "./file.py"


@pytest.mark.utils
def test_normalize_file_path_for_display_parent_dir():
    """Test normalizing a path that goes up directories."""
    with patch("os.getcwd", return_value="/project/root"):
        with patch("os.path.abspath", return_value="/project/file.py"):
            with patch("os.path.relpath", return_value="../file.py"):
                result = normalize_file_path_for_display("/project/file.py")

    assert result == "../file.py"


@pytest.mark.utils
def test_normalize_file_path_for_display_already_relative():
    """Test normalizing a path that already starts with './'."""
    with patch("os.getcwd", return_value="/project/root"):
        with patch("os.path.abspath", return_value="/project/root/src/file.py"):
            with patch("os.path.relpath", return_value="./src/file.py"):
                result = normalize_file_path_for_display("./src/file.py")

    assert result == "./src/file.py"


@pytest.mark.utils
def test_normalize_file_path_for_display_error():
    """Test handling errors in path normalization."""
    with patch("os.path.abspath", side_effect=ValueError("Invalid path")):
        result = normalize_file_path_for_display("invalid/path")

    # Should return original path on error
    assert result == "invalid/path"


@pytest.mark.utils
def test_normalize_file_path_for_display_os_error():
    """Test handling OS errors in path normalization."""
    with patch("os.getcwd", side_effect=OSError("Permission denied")):
        result = normalize_file_path_for_display("src/file.py")

    # Should return original path on error
    assert result == "src/file.py"
