"""Test fixtures for integration tests.

This module provides shared fixtures for integration testing in Lintro.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_files_dir():
    """Provide a directory with test files for integration tests.

    Yields:
        Path: Path to the temporary directory containing test files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)

        # Create test files
        (test_dir / "test.py").write_text("def test_function():\n    pass\n")
        (test_dir / "test.js").write_text(
            "function testFunction() {\n    console.log('test');\n}\n",
        )
        (test_dir / "test.yml").write_text("key: value\nlist:\n  - item1\n  - item2\n")
        (test_dir / "Dockerfile").write_text(
            "FROM python:3.13\nCOPY . .\nRUN pip install -r requirements.txt\n",
        )

        yield test_dir


@pytest.fixture
def sample_python_file():
    """Provide a sample Python file with violations.

    Returns:
        str: Contents of a sample Python file with violations.
    """
    return """def test_function(param1, param2):
    \"\"\"Test function.

    Args:
        param1: First parameter
    \"\"\"
    return param1 + param2
"""


@pytest.fixture
def sample_js_file():
    """Provide a sample JavaScript file with formatting issues.

    Returns:
        str: Contents of a sample JavaScript file with formatting issues.
    """
    return """function testFunction(param1,param2){
return param1+param2;
}"""
