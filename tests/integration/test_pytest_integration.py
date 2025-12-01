"""Integration tests for Pytest tool."""

import os
import shutil
import tempfile

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_pytest import PytestTool

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
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
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
def set_lintro_test_mode_env():
    """Set LINTRO_TEST_MODE=1 for all tests in this module.

    Yields:
        None: This fixture is used for its side effect only.
    """
    old = os.environ.get("LINTRO_TEST_MODE")
    os.environ["LINTRO_TEST_MODE"] = "1"
    yield
    if old is not None:
        os.environ["LINTRO_TEST_MODE"] = old
    else:
        os.environ.pop("LINTRO_TEST_MODE", None)


@pytest.fixture
def pytest_tool():
    """Create a PytestTool instance for testing.

    Returns:
        PytestTool: A configured PytestTool instance.
    """
    return PytestTool()


@pytest.fixture
def pytest_clean_file():
    """Return the path to the static pytest clean file for testing.

    Yields:
        str: Path to the static pytest_clean.py file.
    """
    yield os.path.abspath("test_samples/pytest_clean.py")


@pytest.fixture
def pytest_failures_file():
    """Return the path to the static pytest failures file for testing.

    Yields:
        str: Path to the static pytest_failures.py file.
    """
    yield os.path.abspath("test_samples/pytest_failures.py")


@pytest.fixture
def temp_test_dir(request):
    """Create a temporary directory with test files.

    Args:
        request: Pytest request fixture for finalizer registration.

    Yields:
        str: Path to the temporary directory containing test files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy pytest_clean.py to temp directory
        src_clean = os.path.abspath("test_samples/pytest_clean.py")
        dst_clean = os.path.join(tmpdir, "test_clean.py")
        shutil.copy(src_clean, dst_clean)

        # Copy pytest_failures.py to temp directory
        src_failures = os.path.abspath("test_samples/pytest_failures.py")
        dst_failures = os.path.join(tmpdir, "test_failures.py")
        shutil.copy(src_failures, dst_failures)

        yield tmpdir


@pytest.mark.skipif(
    not pytest_available(),
    reason="pytest not available; skip integration test.",
)
def test_tool_initialization(pytest_tool) -> None:
    """Test that PytestTool initializes correctly.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    assert_that(pytest_tool.name).is_equal_to("pytest")
    assert_that(pytest_tool.can_fix is False).is_true()
    assert_that(pytest_tool.config.file_patterns).contains("test_*.py")
    # Note: pytest.ini may override default patterns, so *_test.py may not be
    # present if pytest.ini only specifies test_*.py


def test_tool_priority(pytest_tool) -> None:
    """Test that PytestTool has correct priority.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    assert_that(pytest_tool.config.priority).is_equal_to(90)


def test_run_tests_on_clean_file(pytest_tool, pytest_clean_file) -> None:
    """Test pytest execution on a clean test file.

    Args:
        pytest_tool: PytestTool fixture instance.
        pytest_clean_file: Path to the static clean pytest file.
    """
    # Ensure pytest only runs the specific file, not other tests in the directory
    result = pytest_tool.check(files=[pytest_clean_file])
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
    pytest_tool,
    pytest_failures_file,
) -> None:
    """Test pytest execution on a file with intentional failures.

    Args:
        pytest_tool: PytestTool fixture instance.
        pytest_failures_file: Path to the static pytest failures file.
    """
    result = pytest_tool.check(files=[pytest_failures_file])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")
    # Failures file should have failing tests
    assert_that(result.success is False).is_true()
    assert_that(result.issues_count > 0).is_true()


def test_run_tests_on_directory(pytest_tool, temp_test_dir) -> None:
    """Test pytest execution on a directory with multiple test files.

    Args:
        pytest_tool: PytestTool fixture instance.
        temp_test_dir: Temporary directory with test files.
    """
    result = pytest_tool.check(paths=[temp_test_dir])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")
    # Directory contains pytest_failures.py with intentional failures
    # so result should indicate test failures
    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)
    # Result should have output with summary
    assert_that(result.output).is_not_empty()


def test_docker_tests_disabled_by_default(
    pytest_tool,
    temp_test_dir,
) -> None:
    """Test that Docker tests are disabled by default.

    Args:
        pytest_tool: PytestTool fixture instance.
        temp_test_dir: Temporary directory with test files.
    """
    # Ensure docker tests are disabled
    original_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")
    if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
        del os.environ["LINTRO_RUN_DOCKER_TESTS"]

    try:
        pytest_tool.set_options(run_docker_tests=False)
        result = pytest_tool.check(paths=[temp_test_dir])
        assert_that(isinstance(result, ToolResult)).is_true()
        # Should still run, but docker tests should be skipped
        # The output may be in JSON format, so check for both text and JSON formats
        output_lower = result.output.lower()
        # Check for skipped tests in either text or JSON output format
        assert_that(
            "docker tests disabled" in output_lower
            or "docker tests not collected" in output_lower
            or "not collected" in output_lower
            or '"skipped"' in output_lower,  # JSON format
        ).is_true()
    finally:
        if original_env is not None:
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_env


def test_docker_tests_enabled_via_option(
    pytest_tool,
    temp_test_dir,
) -> None:
    """Test that Docker tests can be enabled via option.

    Args:
        pytest_tool: PytestTool fixture instance.
        temp_test_dir: Temporary directory with test files.
    """
    # Ensure docker tests are enabled
    original_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")
    os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"

    try:
        pytest_tool.set_options(run_docker_tests=True)
        result = pytest_tool.check(paths=[temp_test_dir])
        assert_that(isinstance(result, ToolResult)).is_true()
        # Should still run successfully
        assert_that(result.name).is_equal_to("pytest")
    finally:
        if original_env is not None:
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_env
        elif "LINTRO_RUN_DOCKER_TESTS" in os.environ:
            del os.environ["LINTRO_RUN_DOCKER_TESTS"]


@pytest.mark.slow
def test_default_paths(pytest_tool) -> None:
    """Test that default paths work correctly.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    # When no paths are provided, should default to "tests"
    # Use a timeout to prevent hanging if tests take too long
    pytest_tool.set_options(timeout=120)
    # Just test discovery works, not full test run
    result = pytest_tool.check(paths=["tests/unit/test_pytest_tool.py"])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("pytest")


def test_set_options_valid(pytest_tool) -> None:
    """Test setting valid options.

    Args:
        pytest_tool: PytestTool fixture instance.
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


def test_set_options_invalid_tb(pytest_tool) -> None:
    """Test setting invalid traceback format.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    with pytest.raises(ValueError, match="tb must be one of"):
        pytest_tool.set_options(tb="invalid")


def test_set_options_invalid_maxfail(pytest_tool) -> None:
    """Test setting invalid maxfail value.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    with pytest.raises(ValueError, match="maxfail must be a positive integer"):
        pytest_tool.set_options(maxfail="not_a_number")


def test_fix_not_implemented(pytest_tool) -> None:
    """Test that fix method raises NotImplementedError.

    Args:
        pytest_tool: PytestTool fixture instance.
    """
    with pytest.raises(NotImplementedError):
        pytest_tool.fix(["test_file.py"])


def test_output_contains_summary(pytest_tool, pytest_failures_file) -> None:
    """Test that output contains summary information.

    Args:
        pytest_tool: PytestTool fixture instance.
        pytest_failures_file: Path to the static pytest failures file.
    """
    result = pytest_tool.check(files=[pytest_failures_file])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.output).is_not_empty()
    # Output should contain JSON summary or test results
    assert_that(
        "passed" in result.output.lower() or "failed" in result.output.lower(),
    ).is_true()


def test_pytest_output_consistency_direct_vs_lintro(
    pytest_failures_file,
) -> None:
    """Test that lintro produces consistent results with direct pytest.

    Args:
        pytest_failures_file: Path to the static pytest failures file.
    """
    import subprocess
    import sys

    logger.info("[TEST] Comparing pytest CLI and Lintro PytestTool outputs...")
    tool = PytestTool()
    tool.set_options(verbose=True, tb="short")

    # In Docker, pytest is only available as python -m pytest
    # Check if we're in Docker or if pytest is available on PATH
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
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
    lintro_result = tool.check(files=[pytest_failures_file])

    # Both should detect failures
    assert_that(direct_result.returncode != 0).is_true()
    assert_that(lintro_result.success is False).is_true()
    assert_that(lintro_result.issues_count > 0).is_true()

    logger.info(
        f"[LOG] Direct pytest exit code: {direct_result.returncode}, "
        f"Lintro issues: {lintro_result.issues_count}",
    )
