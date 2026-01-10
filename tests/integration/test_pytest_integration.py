"""Integration tests for Pytest tool."""

import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.enums.env_bool import EnvBool
from lintro.models.core.tool_result import ToolResult
from lintro.plugins import ToolRegistry
from lintro.plugins.base import BaseToolPlugin

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


def pytest_available() -> bool:
    """Check if pytest is available.

    In Docker, pytest is installed in the venv and should always be available.
    Locally, check if pytest is on PATH or can be imported.

    Returns:
        bool: True if pytest is available, False otherwise.
    """
    # In Docker, pytest should always be available since we control the environment
    if os.environ.get("RUNNING_IN_DOCKER") == EnvBool.TRUE:
        return True

    # Check if pytest is on PATH
    if shutil.which("pytest") is not None:
        return True

    # Check if pytest can be imported as a module
    try:
        import pytest  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set LINTRO_TEST_MODE=1 for all tests in this module.

    Args:
        monkeypatch: Pytest monkeypatch fixture for environment manipulation.
    """
    monkeypatch.setenv("LINTRO_TEST_MODE", "1")


@pytest.fixture
def pytest_tool() -> BaseToolPlugin:
    """Create a PytestTool instance for testing.

    Returns:
        BaseToolPlugin: A configured PytestTool instance.
    """
    tool = ToolRegistry.get("pytest")
    # Remove test_samples from exclude patterns so integration tests can run on sample
    # files
    tool.exclude_patterns = [
        p for p in tool.exclude_patterns if "test_samples" not in p
    ]
    return tool


@pytest.fixture
def pytest_clean_file(tmp_path: Path) -> Generator[str]:
    """Copy pytest clean file to a temp location outside test_samples.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Yields:
        str: Path to the copied pytest_clean.py file.
    """
    src = os.path.abspath("test_samples/tools/python/pytest/pytest_clean.py")
    dst = tmp_path / "pytest_clean.py"
    shutil.copy(src, dst)
    yield str(dst)


@pytest.fixture
def pytest_failures_file(tmp_path: Path) -> Generator[str]:
    """Copy pytest failures file to a temp location outside test_samples.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Yields:
        str: Path to the copied pytest_failures.py file.
    """
    src = os.path.abspath("test_samples/tools/python/pytest/pytest_failures.py")
    dst = tmp_path / "pytest_failures.py"
    shutil.copy(src, dst)
    yield str(dst)


@pytest.fixture
def temp_test_dir(request: pytest.FixtureRequest) -> Generator[str]:
    """Create a temporary directory with test files.

    Args:
        request: Pytest request fixture for finalizer registration.

    Yields:
        str: Path to the temporary directory containing test files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy pytest_clean.py to temp directory
        src_clean = os.path.abspath("test_samples/tools/python/pytest/pytest_clean.py")
        dst_clean = os.path.join(tmpdir, "test_clean.py")
        shutil.copy(src_clean, dst_clean)

        # Copy pytest_failures.py to temp directory
        src_failures = os.path.abspath(
            "test_samples/tools/python/pytest/pytest_failures.py",
        )
        dst_failures = os.path.join(tmpdir, "test_failures.py")
        shutil.copy(src_failures, dst_failures)

        yield tmpdir


@pytest.mark.skipif(
    not pytest_available(),
    reason="pytest not available; skip integration test.",
)
def test_tool_initialization(pytest_tool: BaseToolPlugin) -> None:
    """Test that PytestTool initializes correctly.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    assert_that(pytest_tool.definition.name).is_equal_to("pytest")
    assert_that(pytest_tool.definition.can_fix is False).is_true()
    assert_that(pytest_tool.definition.file_patterns).contains("test_*.py")
    # Note: pytest.ini may override default patterns, so *_test.py may not be
    # present if pytest.ini only specifies test_*.py


def test_tool_priority(pytest_tool: BaseToolPlugin) -> None:
    """Test that PytestTool has correct priority.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    assert_that(pytest_tool.definition.priority).is_equal_to(90)


def test_run_tests_on_clean_file(
    pytest_tool: BaseToolPlugin,
    pytest_clean_file: str,
) -> None:
    """Test pytest execution on a clean test file.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        pytest_clean_file: Path to the static clean pytest file.
    """
    # Ensure pytest only runs the specific file, not other tests in the directory
    result = pytest_tool.check([pytest_clean_file], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")
    # Clean file should have passing tests - allow for some skipped tests if they
    # exist but the main test should pass
    assert_that(result.success is True).described_as(
        f"Expected success=True but got False. Output: {result.output}",
    ).is_true()
    # Issues count should be 0 for clean file
    assert_that(result.issues_count).is_equal_to(0)


def test_run_tests_on_failures_file(
    pytest_tool: BaseToolPlugin,
    pytest_failures_file: str,
) -> None:
    """Test pytest execution on a file with intentional failures.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        pytest_failures_file: Path to the static pytest failures file.
    """
    result = pytest_tool.check([pytest_failures_file], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")
    # Failures file should have failing tests
    assert_that(result.success is False).is_true()
    assert_that(result.issues_count > 0).is_true()


def test_run_tests_on_directory(
    pytest_tool: BaseToolPlugin,
    temp_test_dir: str,
) -> None:
    """Test pytest execution on a directory with multiple test files.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        temp_test_dir: Temporary directory with test files.
    """
    result = pytest_tool.check([temp_test_dir], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")
    # Directory contains pytest_failures.py with intentional failures
    # so result should indicate test failures
    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)
    # Result should have output with summary
    assert_that(result.output).is_not_empty()


def test_docker_tests_disabled_by_default(
    pytest_tool: BaseToolPlugin,
    temp_test_dir: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Docker tests are disabled by default.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        temp_test_dir: Temporary directory with test files.
        monkeypatch: Pytest monkeypatch fixture for environment manipulation.
    """
    # Ensure docker tests are disabled
    monkeypatch.delenv("LINTRO_RUN_DOCKER_TESTS", raising=False)

    pytest_tool.set_options(run_docker_tests=False)
    result = pytest_tool.check([temp_test_dir], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    # Should still run, but docker tests should be skipped
    # The output may be in JSON format, so check for both text and JSON formats
    assert_that(result.output).is_not_none()
    if result.output is None:
        pytest.fail("output should not be None")
    output_lower = result.output.lower()
    # Check for skipped tests in either text or JSON output format
    assert_that(
        "docker tests disabled" in output_lower
        or "docker tests not collected" in output_lower
        or "not collected" in output_lower
        or '"skipped"' in output_lower,  # JSON format
    ).is_true()


def test_docker_tests_enabled_via_option(
    pytest_tool: BaseToolPlugin,
    temp_test_dir: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Docker tests can be enabled via option.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        temp_test_dir: Temporary directory with test files.
        monkeypatch: Pytest monkeypatch fixture for environment manipulation.
    """
    # Ensure docker tests are enabled
    monkeypatch.setenv("LINTRO_RUN_DOCKER_TESTS", "1")

    pytest_tool.set_options(run_docker_tests=True)
    result = pytest_tool.check([temp_test_dir], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    # Should still run successfully
    assert_that(result.name).is_equal_to("pytest")


@pytest.mark.slow
def test_default_paths(pytest_tool: BaseToolPlugin) -> None:
    """Test that default paths work correctly.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    # When no paths are provided, should default to "tests"
    # Use a timeout to prevent hanging if tests take too long
    pytest_tool.set_options(timeout=120)
    # Just test discovery works, not full test run
    result = pytest_tool.check(["tests/unit/test_pytest_tool.py"], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")


def test_set_options_valid(pytest_tool: BaseToolPlugin) -> None:
    """Test setting valid options.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    pytest_tool.set_options(
        verbose=True,
        tb="short",
        maxfail=5,
        no_header=True,
        disable_warnings=True,
    )
    assert_that(pytest_tool.options["verbose"] is True).is_true()
    assert_that(pytest_tool.options["tb"]).is_equal_to("short")
    assert_that(pytest_tool.options["maxfail"]).is_equal_to(5)


def test_set_options_invalid_tb(pytest_tool: BaseToolPlugin) -> None:
    """Test setting invalid traceback format.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    with pytest.raises(ValueError, match="tb must be one of"):
        pytest_tool.set_options(tb="invalid")


def test_set_options_invalid_maxfail(pytest_tool: BaseToolPlugin) -> None:
    """Test setting invalid maxfail value.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    with pytest.raises(ValueError, match="maxfail must be a positive integer"):
        pytest_tool.set_options(maxfail="not_a_number")


def test_fix_not_implemented(pytest_tool: BaseToolPlugin) -> None:
    """Test that fix method raises NotImplementedError.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
    """
    with pytest.raises(NotImplementedError):
        pytest_tool.fix(["test_file.py"], {})


def test_output_contains_summary(
    pytest_tool: BaseToolPlugin,
    pytest_failures_file: str,
) -> None:
    """Test that output contains summary information.

    Args:
        pytest_tool: BaseToolPlugin fixture instance.
        pytest_failures_file: Path to the static pytest failures file.
    """
    result = pytest_tool.check([pytest_failures_file], {})
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.output).is_not_empty()
    # Output should contain JSON summary or test results
    assert_that(result.output).is_not_none()
    if result.output is None:
        pytest.fail("output should not be None")
    assert_that(
        "passed" in result.output.lower() or "failed" in result.output.lower(),
    ).is_true()


def test_pytest_output_consistency_direct_vs_lintro(
    pytest_failures_file: str,
) -> None:
    """Test that lintro produces consistent results with direct pytest.

    Args:
        pytest_failures_file: Path to the static pytest failures file.
    """
    import subprocess
    import sys

    logger.info("[TEST] Comparing pytest CLI and Lintro PytestTool outputs...")
    tool = ToolRegistry.get("pytest")
    tool.set_options(verbose=True, tb="short")

    # In Docker, pytest is only available as python -m pytest
    # Check if we're in Docker or if pytest is available on PATH
    if os.environ.get("RUNNING_IN_DOCKER") == EnvBool.TRUE:
        # Use python -m pytest in Docker
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-v",
            "--tb=short",
            "--no-header",
            pytest_failures_file,
        ]
    else:
        # Use pytest directly if available on PATH
        pytest_cmd = shutil.which("pytest")
        if pytest_cmd is None:
            pytest.skip("pytest not available on PATH for direct comparison")
        cmd = [pytest_cmd, "-v", "--tb=short", "--no-header", pytest_failures_file]

    direct_result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    # Run via lintro
    lintro_result = tool.check([pytest_failures_file], {})

    # Both should detect failures
    assert_that(direct_result.returncode != 0).is_true()
    assert_that(lintro_result.success is False).is_true()
    assert_that(lintro_result.issues_count > 0).is_true()

    logger.info(
        f"[LOG] Direct pytest exit code: {direct_result.returncode}, "
        f"Lintro issues: {lintro_result.issues_count}",
    )
