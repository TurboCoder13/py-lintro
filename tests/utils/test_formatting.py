"""Tests for the formatting utilities module.

This module contains tests for the formatting utility functions in Lintro.
"""

import pytest
from unittest.mock import patch, mock_open

from lintro.utils.formatting import read_ascii_art


@pytest.mark.utils
def test_read_ascii_art():
    """Test reading ASCII art from file."""
    mock_content = "line1\nline2\nline3\n"

    with patch("builtins.open", mock_open(read_data=mock_content)):
        with patch("pathlib.Path.open", mock_open(read_data=mock_content)):
            result = read_ascii_art("test.txt")

    assert result == ["line1", "line2", "line3"]


@pytest.mark.utils
def test_read_ascii_art_file_not_found():
    """Test reading ASCII art when file doesn't exist."""
    result = read_ascii_art("nonexistent.txt")
    assert result == []


@pytest.mark.utils
def test_read_ascii_art_with_sections():
    """Test reading ASCII art file with multiple sections."""
    mock_content = "section1_line1\nsection1_line2\n\nsection2_line1\nsection2_line2\n"

    with patch("builtins.open", mock_open(read_data=mock_content)):
        with patch("pathlib.Path.open", mock_open(read_data=mock_content)):
            with patch("random.choice") as mock_choice:
                mock_choice.return_value = ["section1_line1", "section1_line2"]
                result = read_ascii_art("test.txt")

    assert result == ["section1_line1", "section1_line2"]
    # Verify random.choice was called with the sections
    mock_choice.assert_called_once()
