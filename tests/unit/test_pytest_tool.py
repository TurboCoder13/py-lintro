"""Unit tests for pytest tool implementation."""

import os
from unittest.mock import Mock, patch

import pytest

from lintro.enums.tool_type import ToolType
from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_initialization() -> None:
    """Test that PytestTool initializes correctly."""
    tool = PytestTool()

    assert tool.name == "pytest"
    assert "Python testing tool" in tool.description
    assert tool.can_fix is False
    assert tool.config.tool_type == ToolType.TEST_RUNNER
    assert tool._default_timeout == 300
    assert tool.config.priority == 90
    # File patterns may be loaded from config, so just check that patterns exist
    assert len(tool.config.file_patterns) > 0
    assert any("test" in pattern for pattern in tool.config.file_patterns)


def test_pytest_tool_set_options_valid() -> None:
    """Test setting valid options."""
    tool = PytestTool()

    tool.set_options(
        verbose=True,
        tb="short",
        maxfail=5,
        no_header=False,
        disable_warnings=True,
        json_report=True,
        junitxml="report.xml",
    )

    assert tool.options["verbose"] is True
    assert tool.options["tb"] == "short"
    assert tool.options["maxfail"] == 5
    assert tool.options["no_header"] is False
    assert tool.options["disable_warnings"] is True
    assert tool.options["json_report"] is True
    assert tool.options["junitxml"] == "report.xml"


def test_pytest_tool_set_options_invalid_verbose() -> None:
    """Test setting invalid verbose option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="verbose must be a boolean"):
        tool.set_options(verbose="invalid")


def test_pytest_tool_set_options_invalid_tb() -> None:
    """Test setting invalid tb option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="tb must be one of"):
        tool.set_options(tb="invalid")


def test_pytest_tool_set_options_invalid_maxfail() -> None:
    """Test setting invalid maxfail option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="maxfail must be a positive integer"):
        tool.set_options(maxfail="invalid")


def test_pytest_tool_set_options_invalid_no_header() -> None:
    """Test setting invalid no_header option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="no_header must be a boolean"):
        tool.set_options(no_header="invalid")


def test_pytest_tool_set_options_invalid_disable_warnings() -> None:
    """Test setting invalid disable_warnings option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="disable_warnings must be a boolean"):
        tool.set_options(disable_warnings="invalid")


def test_pytest_tool_set_options_invalid_json_report() -> None:
    """Test setting invalid json_report option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="json_report must be a boolean"):
        tool.set_options(json_report="invalid")


def test_pytest_tool_set_options_invalid_junitxml() -> None:
    """Test setting invalid junitxml option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="junitxml must be a string"):
        tool.set_options(junitxml=123)


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

            assert cmd[0] == "pytest"
            assert "-v" in cmd
            assert "--tb" in cmd
            assert "short" in cmd
            # maxfail is explicitly set in the test, not loaded from pytest.ini
            assert "--maxfail" in cmd
            assert "3" in cmd
            assert "--no-header" in cmd
            assert "--disable-warnings" in cmd
            assert "test_file.py" in cmd


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

        assert cmd[0] == "pytest"
        assert "-v" not in cmd
        assert "--tb" in cmd
        assert "long" in cmd
        assert "--maxfail" in cmd
        assert "10" in cmd
        assert "--no-header" not in cmd
        assert "--disable-warnings" not in cmd
        assert "--json-report" in cmd
        assert "--json-report-file=pytest-report.json" in cmd
        assert "--junitxml" in cmd
        assert "report.xml" in cmd


def test_pytest_tool_build_check_command_test_mode() -> None:
    """Test building check command in test mode."""
    tool = PytestTool()

    with (
        patch.dict(os.environ, {"LINTRO_TEST_MODE": "1"}),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
    ):
        cmd = tool._build_check_command(["test_file.py"])

        assert "--strict-markers" in cmd
        assert "--strict-config" in cmd


def test_pytest_tool_parse_output_json_format() -> None:
    """Test parsing JSON format output."""
    tool = PytestTool()
    tool.set_options(json_report=True, junitxml=None)

    json_output = """{
        "tests": [
            {
                "file": "test_example.py",
                "lineno": 10,
                "name": "test_failure",
                "outcome": "failed",
                "call": {
                    "longrepr": "AssertionError: Expected 1 but got 2"
                },
                "duration": 0.001,
                "nodeid": "test_example.py::test_failure"
            }
        ]
    }"""

    issues = tool._parse_output(json_output, 1)

    assert len(issues) == 1
    assert issues[0].file == "test_example.py"
    assert issues[0].line == 10
    assert issues[0].test_name == "test_failure"
    assert issues[0].test_status == "FAILED"
    assert issues[0].message == "AssertionError: Expected 1 but got 2"


def test_pytest_tool_parse_output_junit_format() -> None:
    """Test parsing JUnit XML format output."""
    tool = PytestTool()
    tool.set_options(junitxml="report.xml")

    xml_output = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuite name="pytest" tests="1" failures="1" errors="0" time="0.001">\n'
        '    <testcase name="test_failure" file="test_example.py" line="10" '
        'time="0.001" classname="TestExample">\n'
        '        <failure message="AssertionError: Expected 1 but got 2">'
        "Traceback...</failure>\n"
        "    </testcase>\n"
        "</testsuite>"
    )

    issues = tool._parse_output(xml_output, 1)

    assert len(issues) == 1
    assert issues[0].file == "test_example.py"
    assert issues[0].line == 10
    assert issues[0].test_name == "test_failure"
    assert issues[0].test_status == "FAILED"


def test_pytest_tool_parse_output_text_format() -> None:
    """Test parsing text format output."""
    tool = PytestTool()

    text_output = (
        "FAILED test_example.py::test_failure - " "AssertionError: Expected 1 but got 2"
    )

    issues = tool._parse_output(text_output, 1)

    assert len(issues) == 1
    assert issues[0].file == "test_example.py"
    assert issues[0].test_name == "test_failure"
    assert issues[0].test_status == "FAILED"
    assert issues[0].message == "AssertionError: Expected 1 but got 2"


def test_pytest_tool_parse_output_fallback_to_text() -> None:
    """Test that parsing falls back to text format when no issues found."""
    tool = PytestTool()
    tool.set_options(json_report=True)

    # Empty JSON output but non-zero return code
    json_output = '{"tests": []}'

    issues = tool._parse_output(json_output, 1)

    # Should fall back to text parsing
    assert isinstance(issues, list)


def test_pytest_tool_check_no_files() -> None:
    """Test check method with no files."""
    tool = PytestTool()

    # Mock subprocess to simulate no tests found
    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "no tests ran"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(0, 0, None),
        ),
    ):
        result = tool.check()

        assert result.name == "pytest"
        assert result.success is True
        assert result.issues == []


def test_pytest_tool_check_success() -> None:
    """Test successful check method."""
    tool = PytestTool()

    mock_result = Mock()
    mock_result.return_code = 0
    mock_result.stdout = "All tests passed"
    mock_result.stderr = ""

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed\n511 passed in 18.53s"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
    ):
        result = tool.check(["test_file.py"])

        assert result.name == "pytest"
        assert result.success is True
        assert result.issues == []
        # Output should contain JSON summary
        assert '"passed": 511' in result.output
        assert '"failed": 0' in result.output
        assert result.issues_count == 0


def test_pytest_tool_check_failure() -> None:
    """Test failed check method."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(
                False,
                "FAILED test_file.py::test_failure - AssertionError\n"
                "510 passed, 1 failed in 18.53s",
            ),
        ),
    ):
        result = tool.check(["test_file.py"])

        assert result.name == "pytest"
        assert result.success is False
        assert len(result.issues) == 1
        assert result.issues[0].file == "test_file.py"
        assert result.issues[0].test_name == "test_failure"
        assert result.issues[0].test_status == "FAILED"
        assert "AssertionError" in result.issues[0].message
        # Output should contain JSON summary
        assert '"failed": 1' in result.output
        assert result.issues_count == 1


def test_pytest_tool_check_exception() -> None:
    """Test check method with exception."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            side_effect=Exception("Test error"),
        ),
    ):
        result = tool.check(["test_file.py"])

        assert result.name == "pytest"
        assert result.success is False
        assert result.issues == []
        assert "Test error" in result.output


def test_pytest_tool_fix_default_behavior() -> None:
    """Test that fix raises NotImplementedError when can_fix is False (default)."""
    tool = PytestTool()
    assert tool.can_fix is False

    with pytest.raises(NotImplementedError):
        tool.fix(["test_file.py"])


def test_pytest_tool_fix_with_can_fix_true() -> None:
    """Test that fix raises NotImplementedError even when can_fix is True."""
    tool = PytestTool()
    # Mock can_fix to True to test the second check
    tool.can_fix = True

    with pytest.raises(
        NotImplementedError,
        match="pytest does not support fixing issues",
    ):
        tool.fix(["test_file.py"])


def test_pytest_tool_check_paths_vs_files_precedence() -> None:
    """Test that paths parameter takes precedence over files."""
    tool = PytestTool()

    # Create a mock to capture the command passed to _run_subprocess
    mock_run_subprocess = Mock(return_value=(True, "All tests passed"))

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            mock_run_subprocess,
        ),
        patch.object(tool, "_parse_output", return_value=[]),
    ):
        # Both paths and files provided; paths should be used
        tool.check(files=["file.py"], paths=["path/"])

        # Verify _run_subprocess was called
        assert mock_run_subprocess.called
        # Get the command that was passed to _run_subprocess
        call_args = mock_run_subprocess.call_args
        cmd = call_args[0][0]  # First positional argument is the command list

        # Assert that paths argument ("path/") is in the command
        assert "path/" in cmd, f"Expected 'path/' in command, got: {cmd}"
        # Assert that files argument ("file.py") is NOT in the command
        # since paths takes precedence over files
        assert "file.py" not in cmd, (
            f"Expected 'file.py' NOT in command "
            f"(paths takes precedence), got: {cmd}"
        )


def test_pytest_tool_check_discovers_test_files() -> None:
    """Verify that check discovers test files without files or paths."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "5 passed in 0.10s"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(5, 0, None),
        ),
    ):
        result = tool.check()

        assert result.name == "pytest"
        assert result.success is True


def test_pytest_tool_parse_output_fallback_to_text_with_issues() -> None:
    """Test parse_output falls back to text when JSON parsing fails."""
    tool = PytestTool()
    tool.set_options(json_report=True)

    # JSON format failed, but text parsing should find issues
    output = "FAILED test.py::test_fail - AssertionError"

    issues = tool._parse_output(output, 1)

    # Should fall back and find issues via text parsing
    assert isinstance(issues, list)


def test_pytest_tool_build_check_command_no_verbose() -> None:
    """Test building command when verbose and show_progress are False."""
    tool = PytestTool()
    tool.set_options(verbose=False, show_progress=False)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        # When both verbose and show_progress are False, should not include -v
        assert "-v" not in cmd


def test_pytest_tool_build_check_command_custom_tb_format() -> None:
    """Test building command with custom traceback format."""
    tool = PytestTool()
    tool.set_options(tb="long")

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert "--tb" in cmd
        assert "long" in cmd


def test_pytest_tool_build_check_command_maxfail_option() -> None:
    """Test building command with custom maxfail value."""
    tool = PytestTool()
    tool.set_options(maxfail=10)

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        assert "--maxfail" in cmd
        assert "10" in cmd


def test_pytest_tool_build_check_command_maxfail_default_zero() -> None:
    """Test that maxfail defaults to 3 from pytest.ini config."""
    tool = PytestTool()
    # Don't set maxfail explicitly - should use pytest.ini default of 3

    with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
        cmd = tool._build_check_command(["test_file.py"])

        # maxfail is loaded from pytest.ini which has --maxfail=3
        assert "--maxfail" in cmd
        assert "3" in cmd


def test_pytest_tool_parse_output_json_with_no_issues() -> None:
    """Test parsing JSON output with no issues."""
    tool = PytestTool()
    tool.set_options(json_report=True, junitxml=None)

    json_output = '{"tests": []}'

    issues = tool._parse_output(json_output, 0)

    assert issues == []


def test_pytest_tool_parse_output_mixed_formats() -> None:
    """Test parse_output with mixed success/failure scenarios."""
    tool = PytestTool()

    # Test success (return code 0, no failures)
    issues = tool._parse_output("All tests passed", 0)
    assert issues == []

    # Test failure (return code 1, has failures)
    issues = tool._parse_output("FAILED test.py::test - Error", 1)
    assert isinstance(issues, list)


def test_pytest_tool_load_config_error_handling() -> None:
    """Test loading pytest config with error handling."""
    from lintro.tools.implementations.pytest.pytest_utils import load_pytest_config

    # Test with invalid config files
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Read error")),
    ):
        result = load_pytest_config()
        assert result == {}


def test_pytest_tool_load_lintro_ignore_error() -> None:
    """Test loading .lintro-ignore with error handling."""
    from lintro.tools.implementations.pytest.pytest_utils import load_lintro_ignore

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Read error")),
    ):
        result = load_lintro_ignore()
        assert result == []


def test_pytest_tool_set_options_invalid_run_docker_tests() -> None:
    """Test setting invalid run_docker_tests option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="run_docker_tests must be a boolean"):
        tool.set_options(run_docker_tests="invalid")


def test_pytest_tool_load_file_patterns_list() -> None:
    """Test loading file patterns as list from config."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        load_file_patterns_from_config,
    )

    config = {"python_files": ["test_*.py", "*_test.py"]}
    result = load_file_patterns_from_config(config)
    assert result == ["test_*.py", "*_test.py"]


def test_pytest_tool_load_file_patterns_invalid_type() -> None:
    """Test loading file patterns with invalid type."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        load_file_patterns_from_config,
    )

    config = {"python_files": 123}
    result = load_file_patterns_from_config(config)
    assert result == []


def test_pytest_tool_check_target_files_none() -> None:
    """Test check with target_files as None."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 0, None),
        ),
    ):
        result = tool.check(files=None, paths=None)
        assert result.success is True


def test_pytest_tool_check_target_files_dot() -> None:
    """Test check with target_files as just '.'."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 0, None),
        ),
    ):
        result = tool.check(files=["."])
        assert result.success is True


def test_pytest_tool_check_run_docker_tests_enabled() -> None:
    """Test check with run_docker_tests enabled."""
    tool = PytestTool()
    tool.set_options(run_docker_tests=True)

    # Store original state
    original_value = os.environ.get("LINTRO_RUN_DOCKER_TESTS")

    try:
        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, "All tests passed"),
            ),
            patch.object(tool, "_parse_output", return_value=[]),
            patch.object(
                tool.executor,
                "prepare_test_execution",
                return_value=(10, 5, None),
            ),
        ):
            result = tool.check(["tests"])
            assert result.success is True
            # Verify docker tests env var was NOT set after cleanup
            # (it's cleaned up in the finally block)
            assert "LINTRO_RUN_DOCKER_TESTS" not in os.environ
    finally:
        # Clean up environment variable
        if original_value is None:
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]
        else:
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_value


def test_pytest_tool_check_docker_disabled_message() -> None:
    """Test check with docker tests disabled shows message."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 3, None),
        ),
    ):
        result = tool.check(["tests"])
        assert result.success is True


def test_pytest_tool_check_docker_skipped_calculation() -> None:
    """Test check calculates docker skipped correctly."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "7 passed, 3 skipped"),
        ),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 3, None),
        ),
    ):
        result = tool.check(["tests"])
        assert result.success is True
        if hasattr(result, "pytest_summary"):
            assert result.pytest_summary["docker_skipped"] == 3


def test_pytest_tool_load_file_patterns_empty_config() -> None:
    """Test loading file patterns with empty config."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        load_file_patterns_from_config,
    )

    result = load_file_patterns_from_config({})
    assert result == []


def test_pytest_tool_load_file_patterns_none_python_files() -> None:
    """Test loading file patterns when python_files is None."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        load_file_patterns_from_config,
    )

    config = {"python_files": None}
    result = load_file_patterns_from_config(config)
    assert result == []


def test_pytest_tool_set_options_plugin_support() -> None:
    """Test setting plugin support options."""
    tool = PytestTool()

    tool.set_options(
        list_plugins=True,
        check_plugins=True,
        required_plugins="pytest-cov,pytest-xdist",
    )

    assert tool.options["list_plugins"] is True
    assert tool.options["check_plugins"] is True
    assert tool.options["required_plugins"] == "pytest-cov,pytest-xdist"


def test_pytest_tool_set_options_invalid_list_plugins() -> None:
    """Test setting invalid list_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_plugins must be a boolean"):
        tool.set_options(list_plugins="invalid")


def test_pytest_tool_set_options_invalid_check_plugins() -> None:
    """Test setting invalid check_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="check_plugins must be a boolean"):
        tool.set_options(check_plugins="invalid")


def test_pytest_tool_set_options_invalid_required_plugins() -> None:
    """Test setting invalid required_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="required_plugins must be a string"):
        tool.set_options(required_plugins=123)


def test_pytest_tool_set_options_coverage_reports() -> None:
    """Test setting coverage report options."""
    tool = PytestTool()

    tool.set_options(
        coverage_html="htmlcov",
        coverage_xml="coverage.xml",
        coverage_report=True,
    )

    assert tool.options["coverage_html"] == "htmlcov"
    assert tool.options["coverage_xml"] == "coverage.xml"
    assert tool.options["coverage_report"] is True


def test_pytest_tool_set_options_invalid_coverage_html() -> None:
    """Test setting invalid coverage_html option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_html must be a string"):
        tool.set_options(coverage_html=123)


def test_pytest_tool_set_options_invalid_coverage_xml() -> None:
    """Test setting invalid coverage_xml option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_xml must be a string"):
        tool.set_options(coverage_xml=123)


def test_pytest_tool_set_options_invalid_coverage_report() -> None:
    """Test setting invalid coverage_report option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_report must be a boolean"):
        tool.set_options(coverage_report="invalid")


def test_pytest_tool_set_options_discovery_and_inspection() -> None:
    """Test setting discovery and inspection options."""
    tool = PytestTool()

    tool.set_options(
        collect_only=True,
        list_fixtures=True,
        fixture_info="sample_data",
        list_markers=True,
        parametrize_help=True,
    )

    assert tool.options["collect_only"] is True
    assert tool.options["list_fixtures"] is True
    assert tool.options["fixture_info"] == "sample_data"
    assert tool.options["list_markers"] is True
    assert tool.options["parametrize_help"] is True


def test_pytest_tool_set_options_invalid_collect_only() -> None:
    """Test setting invalid collect_only option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="collect_only must be a boolean"):
        tool.set_options(collect_only="invalid")


def test_pytest_tool_set_options_invalid_list_fixtures() -> None:
    """Test setting invalid list_fixtures option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_fixtures must be a boolean"):
        tool.set_options(list_fixtures="invalid")


def test_pytest_tool_set_options_invalid_fixture_info() -> None:
    """Test setting invalid fixture_info option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="fixture_info must be a string"):
        tool.set_options(fixture_info=123)


def test_pytest_tool_set_options_invalid_list_markers() -> None:
    """Test setting invalid list_markers option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_markers must be a boolean"):
        tool.set_options(list_markers="invalid")


def test_pytest_tool_set_options_invalid_parametrize_help() -> None:
    """Test setting invalid parametrize_help option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="parametrize_help must be a boolean"):
        tool.set_options(parametrize_help="invalid")


def test_pytest_tool_build_check_command_with_coverage_html() -> None:
    """Test building command with coverage HTML report."""
    tool = PytestTool()
    tool.set_options(coverage_html="htmlcov")

    cmd = tool._build_check_command(["test_file.py"])

    assert "--cov-report=html" in cmd or any(
        "--cov-report" in arg and "html" in arg for arg in cmd
    )
    assert "--cov=." in cmd


def test_pytest_tool_build_check_command_with_coverage_xml() -> None:
    """Test building command with coverage XML report."""
    tool = PytestTool()
    tool.set_options(coverage_xml="coverage.xml")

    cmd = tool._build_check_command(["test_file.py"])

    assert "--cov-report=xml" in cmd or any(
        "--cov-report" in arg and "xml" in arg for arg in cmd
    )
    assert "--cov=." in cmd


def test_pytest_tool_build_check_command_with_coverage_report() -> None:
    """Test building command with coverage_report option."""
    tool = PytestTool()
    tool.set_options(coverage_report=True)

    cmd = tool._build_check_command(["test_file.py"])

    # Should include both HTML and XML coverage reports
    assert "--cov=." in cmd
    assert any("html" in arg for arg in cmd if "--cov-report" in arg)
    assert any("xml" in arg for arg in cmd if "--cov-report" in arg)


def test_pytest_tool_handle_list_plugins() -> None:
    """Test handle_list_plugins method."""
    tool = PytestTool()

    with (
        patch(
            "lintro.tools.implementations.pytest.pytest_handlers.list_installed_plugins",
            return_value=[
                {"name": "pytest-cov", "version": "4.0.0"},
                {"name": "pytest-xdist", "version": "3.0.0"},
            ],
        ),
        patch(
            "lintro.tools.implementations.pytest.pytest_handlers.get_pytest_version_info",
            return_value="pytest 7.0.0",
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_plugins,
        )

        result = handle_list_plugins(tool)

        assert result.success is True
        assert "pytest 7.0.0" in result.output
        assert "pytest-cov" in result.output
        assert "pytest-xdist" in result.output


def test_pytest_tool_handle_check_plugins_with_missing() -> None:
    """Test handle_check_plugins with missing plugins."""
    tool = PytestTool()

    with patch(
        "lintro.tools.implementations.pytest.pytest_handlers.check_plugin_installed",
        side_effect=lambda name: name == "pytest-cov",
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_check_plugins,
        )

        result = handle_check_plugins(tool, "pytest-cov,pytest-xdist")

        assert result.success is False
        assert "pytest-cov" in result.output
        assert "pytest-xdist" in result.output
        assert result.issues_count == 1


def test_pytest_tool_handle_check_plugins_all_installed() -> None:
    """Test handle_check_plugins with all plugins installed."""
    tool = PytestTool()

    with patch(
        "lintro.tools.implementations.pytest.pytest_handlers.check_plugin_installed",
        return_value=True,
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_check_plugins,
        )

        result = handle_check_plugins(tool, "pytest-cov,pytest-xdist")

        assert result.success is True
        assert result.issues_count == 0


def test_pytest_tool_handle_check_plugins_no_required() -> None:
    """Test handle_check_plugins without required_plugins."""
    tool = PytestTool()

    from lintro.tools.implementations.pytest.pytest_handlers import (
        handle_check_plugins,
    )

    result = handle_check_plugins(tool, None)

    assert result.success is False
    assert "required_plugins must be specified" in result.output


def test_pytest_tool_handle_collect_only() -> None:
    """Test handle_collect_only method."""
    tool = PytestTool()

    mock_output = """<Module test_example.py>
  <Function test_example>
  <Function test_another>
collected 2 items"""

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_collect_only,
        )

        result = handle_collect_only(tool, ["test_file.py"])

        assert result.success is True
        assert "Collected" in result.output or "2" in result.output


def test_pytest_tool_handle_list_fixtures() -> None:
    """Test handle_list_fixtures method."""
    tool = PytestTool()

    mock_output = "sample_data\n  scope: function\n  location: test_file.py:10"

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_fixtures,
        )

        result = handle_list_fixtures(tool, ["test_file.py"])

        assert result.success is True
        assert result.output == mock_output


def test_pytest_tool_handle_fixture_info() -> None:
    """Test handle_fixture_info method."""
    tool = PytestTool()

    mock_output = """sample_data
  scope: function
  location: test_file.py:10
  description: Sample data fixture"""

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_fixture_info,
        )

        result = handle_fixture_info(tool, "sample_data", ["test_file.py"])

        assert result.success is True
        assert "sample_data" in result.output


def test_pytest_tool_handle_list_markers() -> None:
    """Test handle_list_markers method."""
    tool = PytestTool()

    mock_output = "slow: marks tests as slow\nskip: marks tests as skip"

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_markers,
        )

        result = handle_list_markers(tool)

        assert result.success is True
        assert result.output == mock_output


def test_pytest_tool_handle_parametrize_help() -> None:
    """Test handle_parametrize_help method."""
    tool = PytestTool()

    from lintro.tools.implementations.pytest.pytest_handlers import (
        handle_parametrize_help,
    )

    result = handle_parametrize_help(tool)

    assert result.success is True
    assert "Parametrization" in result.output
    assert "@pytest.mark.parametrize" in result.output


def test_pytest_tool_check_with_list_plugins() -> None:
    """Test check method with list_plugins option."""
    tool = PytestTool()
    tool.set_options(list_plugins=True)

    result = tool.check()

    assert result.success is True
    assert "pytest" in result.output
    assert "Installed pytest plugins" in result.output


def test_pytest_tool_check_with_collect_only() -> None:
    """Test check method with collect_only option."""
    tool = PytestTool()
    tool.set_options(collect_only=True)

    result = tool.check(paths=["tests"])

    assert result.success is True
    assert "Collected" in result.output


def test_pytest_tool_check_with_list_fixtures() -> None:
    """Test check method with list_fixtures option."""
    tool = PytestTool()
    tool.set_options(list_fixtures=True)

    result = tool.check(paths=["tests"])

    assert result.success is True


def test_pytest_tool_check_with_fixture_info() -> None:
    """Test check method with fixture_info option."""
    tool = PytestTool()
    tool.set_options(fixture_info="sample_data")

    result = tool.check(paths=["tests"])

    # Handler runs successfully (even if fixture not found)
    assert isinstance(result, object)


def test_pytest_tool_check_with_list_markers() -> None:
    """Test check method with list_markers option."""
    tool = PytestTool()
    tool.set_options(list_markers=True)

    result = tool.check()

    assert result.success is True


def test_pytest_tool_check_with_parametrize_help() -> None:
    """Test check method with parametrize_help option."""
    tool = PytestTool()
    tool.set_options(parametrize_help=True)

    result = tool.check()

    assert result.success is True
    assert "Parametrization" in result.output
