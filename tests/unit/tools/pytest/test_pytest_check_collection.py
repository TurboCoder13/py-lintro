"""Unit tests for pytest tool test collection functionality."""

import os
from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


def test_collect_tests_once_single_pass(tmp_path: Path) -> None:
    """Test that collect_tests_once performs only a single pytest --collect-only call.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    from lintro.tools.implementations.pytest.markers import collect_tests_once

    # Create test files
    (tmp_path / "test_example.py").write_text(
        """
def test_one():
    pass

def test_two():
    pass""",
    )

    (tmp_path / "docker").mkdir()
    (tmp_path / "docker" / "test_docker.py").write_text(
        """
def test_docker_one():
    pass""",
    )

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        tool = PytestTool()

        # Simulate successful collection output in pytest --collect-only format
        mock_output = """<Module test_example.py>
  <Function test_one>
  <Function test_two>
<Dir docker>
  <Function test_docker_one>

3 tests collected in 0.01s"""

        with patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ) as mock_subprocess:
            # Call collect_tests_once
            total_count, docker_count = collect_tests_once(tool, ["."])

            # Verify only one subprocess call was made
            assert_that(mock_subprocess.call_count).is_equal_to(1)

            # Verify correct counts were extracted
            assert_that(total_count).is_equal_to(3)
            assert_that(docker_count).is_equal_to(1)

    finally:
        os.chdir(original_cwd)


def test_collect_tests_once_no_tests(tmp_path: Path) -> None:
    """Test collect_tests_once with no tests found.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    from lintro.tools.implementations.pytest.markers import collect_tests_once

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        tool = PytestTool()

        with patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "no tests collected in 0.01s"),
        ):
            total_count, docker_count = collect_tests_once(tool, ["."])

            assert_that(total_count).is_equal_to(0)
            assert_that(docker_count).is_equal_to(0)

    finally:
        os.chdir(original_cwd)


def test_collect_tests_once_only_docker_tests(tmp_path: Path) -> None:
    """Test collect_tests_once with only docker tests.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    from lintro.tools.implementations.pytest.markers import collect_tests_once

    # Create only docker tests
    (tmp_path / "docker").mkdir()
    (tmp_path / "docker" / "test_docker.py").write_text(
        """
def test_docker_one():
    pass

def test_docker_two():
    pass""",
    )

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        tool = PytestTool()

        # Mock subprocess for docker tests only
        mock_output = """<Dir docker>
  <Function test_docker_one>
  <Function test_docker_two>

2 tests collected in 0.01s"""

        with patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ):
            total_count, docker_count = collect_tests_once(tool, ["."])

            assert_that(total_count).is_equal_to(2)
            assert_that(docker_count).is_equal_to(2)

    finally:
        os.chdir(original_cwd)


def test_collect_tests_once_mixed_tests(tmp_path: Path) -> None:
    """Test collect_tests_once with mixed regular and docker tests.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    from lintro.tools.implementations.pytest.markers import collect_tests_once

    # Create mixed tests
    (tmp_path / "test_regular.py").write_text(
        """
def test_regular():
    pass""",
    )

    (tmp_path / "docker").mkdir()
    (tmp_path / "docker" / "test_docker.py").write_text(
        """
def test_docker():
    pass""",
    )

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        tool = PytestTool()

        # Mock subprocess for mixed tests
        mock_output = """<Module test_regular.py>
  <Function test_regular>
<Dir docker>
  <Function test_docker>

2 tests collected in 0.01s"""

        with patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ):
            total_count, docker_count = collect_tests_once(tool, ["."])

            assert_that(total_count).is_equal_to(2)
            assert_that(docker_count).is_equal_to(1)

    finally:
        os.chdir(original_cwd)
