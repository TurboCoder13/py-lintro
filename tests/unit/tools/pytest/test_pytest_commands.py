"""Unit tests for pytest tool command building functionality."""

from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_build_check_command_basic() -> None:
    """Test building basic check command."""
    # Patch initialize_pytest_tool_config to prevent loading pytest.ini
    # This isolates the test from the repository's pytest.ini config
    with patch(
        "lintro.tools.implementations.tool_pytest.initialize_pytest_tool_config",
    ):
        tool = PytestTool()
        # Explicitly set maxfail to test command building without config dependency
        tool.set_options(maxfail=3)

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            assert_that(cmd[0]).is_equal_to("pytest")
            assert_that(cmd).contains("-v")
            assert_that(cmd).contains("--tb")
            assert_that(cmd).contains("short")
            # maxfail is explicitly set in the test, not loaded from pytest.ini
            assert_that(cmd).contains("--maxfail")
            assert_that(cmd).contains("3")
            assert_that(cmd).contains("--no-header")
            assert_that(cmd).contains("--disable-warnings")
            assert_that(cmd).contains("test_file.py")


def test_pytest_tool_build_check_command_with_options() -> None:
    """Test building check command with custom options."""
    tool = PytestTool()
    tool.set_options(
        verbose=False,
        show_progress=False,  # Explicitly disable progress to avoid -v
        tb="long",
        maxfail=10,
        no_header=False,
        disable_warnings=False,
        json_report=True,
        junitxml="report.xml",
    )

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd[0]).is_equal_to("pytest")
        assert_that(cmd).does_not_contain("-v")
        assert_that(cmd).contains("--tb")
        assert_that(cmd).contains("long")
        assert_that(cmd).contains("--maxfail")
        assert_that(cmd).contains("10")
        assert_that(cmd).does_not_contain("--no-header")
        assert_that(cmd).does_not_contain("--disable-warnings")
        assert_that(cmd).contains("--json-report")
        assert_that(cmd).contains("--json-report-file=pytest-report.json")
        assert_that(cmd).contains("--junitxml")
        assert_that(cmd).contains("report.xml")


def test_pytest_tool_build_check_command_test_mode() -> None:
    """Test building check command in test mode."""
    tool = PytestTool()

    with (
        patch.dict("os.environ", {"LINTRO_TEST_MODE": "1"}),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
    ):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--strict-markers")
        assert_that(cmd).contains("--strict-config")


def test_pytest_tool_build_check_command_with_timeout() -> None:
    """Test building check command with timeout options."""
    tool = PytestTool()
    tool.set_options(timeout=300)

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch(
            "lintro.tools.implementations.pytest.pytest_command_builder.check_plugin_installed",
            return_value=True,
        ),
    ):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--timeout")
        assert_that(cmd).contains("300")
        assert_that(cmd).contains("--timeout-method")
        assert_that(cmd).contains("signal")  # default method


def test_pytest_tool_build_check_command_with_reruns() -> None:
    """Test building check command with reruns options."""
    tool = PytestTool()
    tool.set_options(reruns=2, reruns_delay=1)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--reruns")
        assert_that(cmd).contains("2")
        assert_that(cmd).contains("--reruns-delay")
        assert_that(cmd).contains("1")


def test_pytest_tool_build_check_command_with_reruns_no_delay() -> None:
    """Test building check command with reruns but no delay."""
    tool = PytestTool()
    tool.set_options(reruns=3)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--reruns")
        assert_that(cmd).contains("3")
        assert_that(cmd).does_not_contain("--reruns-delay")


def test_pytest_tool_build_check_command_no_verbose() -> None:
    """Test building command when verbose and show_progress are False."""
    tool = PytestTool()
    tool.set_options(verbose=False, show_progress=False)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        # When both verbose and show_progress are False, should not include -v
        assert_that(cmd).does_not_contain("-v")


def test_pytest_tool_build_check_command_custom_tb_format() -> None:
    """Test building command with custom traceback format."""
    tool = PytestTool()
    tool.set_options(tb="long")

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--tb")
        assert_that(cmd).contains("long")


def test_pytest_tool_build_check_command_maxfail_option() -> None:
    """Test building command with custom maxfail value."""
    tool = PytestTool()
    tool.set_options(maxfail=10)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert_that(cmd).contains("--maxfail")
        assert_that(cmd).contains("10")


def test_pytest_tool_build_check_command_maxfail_default_zero() -> None:
    """Test that maxfail is not included by default (avoids stopping early)."""
    tool = PytestTool()
    # Don't set maxfail explicitly - should not include maxfail to run all tests

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        # maxfail is not included by default to avoid stopping early
        assert_that(cmd).does_not_contain("--maxfail")


def test_pytest_tool_build_check_command_with_coverage_html() -> None:
    """Test building command with coverage HTML report."""
    tool = PytestTool()
    tool.set_options(coverage_html="htmlcov")

    cmd = tool._build_check_command(["test_file.py"])

    assert_that(
        "--cov-report=html" in cmd
        or any("--cov-report" in arg and "html" in arg for arg in cmd),
    ).is_true()
    assert_that(cmd).contains("--cov=.")


def test_pytest_tool_build_check_command_with_coverage_xml() -> None:
    """Test building command with coverage XML report."""
    tool = PytestTool()
    tool.set_options(coverage_xml="coverage.xml")

    cmd = tool._build_check_command(["test_file.py"])

    assert_that(
        "--cov-report=xml" in cmd
        or any("--cov-report" in arg and "xml" in arg for arg in cmd),
    ).is_true()
    assert_that(cmd).contains("--cov=.")


def test_pytest_tool_build_check_command_with_coverage_report() -> None:
    """Test building command with coverage_report option."""
    tool = PytestTool()
    tool.set_options(coverage_report=True)

    cmd = tool._build_check_command(["test_file.py"])

    # Should include both HTML and XML coverage reports
    assert_that(cmd).contains("--cov=.")
    assert_that(any("html" in arg for arg in cmd if "--cov-report" in arg)).is_true()
    assert_that(any("xml" in arg for arg in cmd if "--cov-report" in arg)).is_true()
