"""Tests for the formatting utilities module.

This module contains tests for the formatting utility functions in Lintro.
"""

from unittest.mock import mock_open, patch

import pytest
from assertpy import assert_that

from lintro.utils.formatting import read_ascii_art


@pytest.mark.utils
def test_read_ascii_art() -> None:
    """Test reading ASCII art from file."""
    mock_content = "line1\nline2\nline3\n"
    with (
        patch("builtins.open", mock_open(read_data=mock_content)),
        patch("pathlib.Path.open", mock_open(read_data=mock_content)),
    ):
        result = read_ascii_art("test.txt")
    assert_that(result).is_equal_to(["line1", "line2", "line3"])


@pytest.mark.utils
def test_read_ascii_art_file_not_found() -> None:
    """Test reading ASCII art when file doesn't exist."""
    result = read_ascii_art("nonexistent.txt")
    assert_that(result).is_equal_to([])


@pytest.mark.utils
def test_read_ascii_art_with_sections() -> None:
    """Test reading ASCII art file with multiple sections."""
    mock_content = "section1_line1\nsection1_line2\n\nsection2_line1\nsection2_line2\n"
    with (
        patch("builtins.open", mock_open(read_data=mock_content)),
        patch("pathlib.Path.open", mock_open(read_data=mock_content)),
        patch("secrets.choice") as mock_choice,
    ):
        mock_choice.return_value = ["section1_line1", "section1_line2"]
        result = read_ascii_art("test.txt")
    assert_that(result).is_equal_to(["section1_line1", "section1_line2"])
    mock_choice.assert_called_once()
