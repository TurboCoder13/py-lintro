"""Tests for the path utilities module."""

from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.path_utils import normalize_file_path_for_display


@pytest.mark.utils
def test_normalize_file_path_for_display_absolute() -> None:
    """Test normalizing an absolute path."""
    with (
        patch("os.getcwd", return_value="/project/root"),
        patch("os.path.abspath", return_value="/project/root/src/file.py"),
        patch("os.path.relpath", return_value="src/file.py"),
    ):
        result = normalize_file_path_for_display("/project/root/src/file.py")
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_relative() -> None:
    """Test normalizing a relative path."""
    with (
        patch("os.getcwd", return_value="/project/root"),
        patch("os.path.abspath", return_value="/project/root/src/file.py"),
        patch("os.path.relpath", return_value="src/file.py"),
    ):
        result = normalize_file_path_for_display("src/file.py")
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_current_dir() -> None:
    """Test normalizing a file in current directory."""
    with (
        patch("os.getcwd", return_value="/project/root"),
        patch("os.path.abspath", return_value="/project/root/file.py"),
        patch("os.path.relpath", return_value="file.py"),
    ):
        result = normalize_file_path_for_display("file.py")
    assert_that(result).is_equal_to("./file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_parent_dir() -> None:
    """Test normalizing a path that goes up directories."""
    with (
        patch("os.getcwd", return_value="/project/root"),
        patch("os.path.abspath", return_value="/project/file.py"),
        patch("os.path.relpath", return_value="../file.py"),
    ):
        result = normalize_file_path_for_display("/project/file.py")
    assert_that(result).is_equal_to("../file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_already_relative() -> None:
    """Test normalizing a path that already starts with './'."""
    with (
        patch("os.getcwd", return_value="/project/root"),
        patch("os.path.abspath", return_value="/project/root/src/file.py"),
        patch("os.path.relpath", return_value="./src/file.py"),
    ):
        result = normalize_file_path_for_display("./src/file.py")
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_error() -> None:
    """Test handling errors in path normalization."""
    with patch("os.path.abspath", side_effect=ValueError("Invalid path")):
        result = normalize_file_path_for_display("invalid/path")
    assert_that(result).is_equal_to("invalid/path")


@pytest.mark.utils
def test_normalize_file_path_for_display_os_error() -> None:
    """Test handling OS errors in path normalization."""
    with patch("os.getcwd", side_effect=OSError("Permission denied")):
        result = normalize_file_path_for_display("src/file.py")
    assert_that(result).is_equal_to("src/file.py")
