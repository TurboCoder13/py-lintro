"""Test fixtures for integration tests.

This module provides shared fixtures for integration testing in Lintro.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def skip_config_injection():
    """Disable Lintro config injection for isolated test execution.

    This fixture sets LINTRO_SKIP_CONFIG_INJECTION=1 to prevent Lintro
    from injecting configuration during tests, allowing tests to verify
    specific CLI argument building behavior.

    Yields:
        None: This fixture is used for its side effect only.
    """
    original = os.environ.get("LINTRO_SKIP_CONFIG_INJECTION")
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("LINTRO_SKIP_CONFIG_INJECTION", None)
        else:
            os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = original


@pytest.fixture
def lintro_test_mode():
    """Set LINTRO_TEST_MODE=1 and disable config injection for all tests.

    This combined fixture sets both LINTRO_TEST_MODE=1 and disables
    config injection, which is commonly needed for ruff integration tests.

    Yields:
        None: This fixture is used for its side effect only.
    """
    old_test_mode = os.environ.get("LINTRO_TEST_MODE")
    old_skip_injection = os.environ.get("LINTRO_SKIP_CONFIG_INJECTION")
    os.environ["LINTRO_TEST_MODE"] = "1"
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    try:
        yield
    finally:
        if old_test_mode is not None:
            os.environ["LINTRO_TEST_MODE"] = old_test_mode
        else:
            os.environ.pop("LINTRO_TEST_MODE", None)

        if old_skip_injection is not None:
            os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = old_skip_injection
        else:
            os.environ.pop("LINTRO_SKIP_CONFIG_INJECTION", None)


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
def sample_python_file() -> str:
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
def sample_js_file() -> str:
    """Provide a sample JavaScript file with formatting issues.

    Returns:
        str: Contents of a sample JavaScript file with formatting issues.
    """
    return """function testFunction(param1,param2){
return param1+param2;
}"""
