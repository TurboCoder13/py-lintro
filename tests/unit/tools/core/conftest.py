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
    # NOTE: Long lines below are intentional test data for E501 detection
    content = '''"""Test module."""

x = 1
y = 2

# This is a long comment that exceeds 88 chars and triggers E501
long_string = "This is a very long string that exceeds the limit"
'''  # noqa: E501
    file_path.write_text(content)
    return file_path
