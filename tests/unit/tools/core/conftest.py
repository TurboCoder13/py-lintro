"""Fixtures for tools/core tests."""

import pytest


@pytest.fixture
def temp_python_file(tmp_path):
    """Create a temporary Python file with long lines for testing.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the temporary Python file.
    """
    file_path = tmp_path / "test_file.py"
    # Create a file with lines of varying lengths
    content = '''"""Test module."""

x = 1
y = 2

# This is a very long comment that exceeds the default line length of 88 characters and should trigger E501
long_string = "This is a very very very very very very very very very long string that exceeds the limit"
'''
    file_path.write_text(content)
    return file_path
