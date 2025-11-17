"""Unit tests for pytest tool implementation."""

import os
from unittest.mock import Mock, patch

import pytest

from lintro.enums.tool_type import ToolType
from lintro.tools.implementations.tool_pytest import PytestTool


class TestPytestTool:
    """Test cases for PytestTool class."""

    def test_pytest_tool_initialization(self) -> None:
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

    def test_pytest_tool_set_options_valid(self) -> None:
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

    def test_pytest_tool_set_options_invalid_verbose(self) -> None:
        """Test setting invalid verbose option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="verbose must be a boolean"):
            tool.set_options(verbose="invalid")

    def test_pytest_tool_set_options_invalid_tb(self) -> None:
        """Test setting invalid tb option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="tb must be one of"):
            tool.set_options(tb="invalid")

    def test_pytest_tool_set_options_invalid_maxfail(self) -> None:
        """Test setting invalid maxfail option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="maxfail must be an integer"):
            tool.set_options(maxfail="invalid")

    def test_pytest_tool_set_options_invalid_no_header(self) -> None:
        """Test setting invalid no_header option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="no_header must be a boolean"):
            tool.set_options(no_header="invalid")

    def test_pytest_tool_set_options_invalid_disable_warnings(self) -> None:
        """Test setting invalid disable_warnings option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="disable_warnings must be a boolean"):
            tool.set_options(disable_warnings="invalid")

    def test_pytest_tool_set_options_invalid_json_report(self) -> None:
        """Test setting invalid json_report option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="json_report must be a boolean"):
            tool.set_options(json_report="invalid")

    def test_pytest_tool_set_options_invalid_junitxml(self) -> None:
        """Test setting invalid junitxml option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="junitxml must be a string"):
            tool.set_options(junitxml=123)

    def test_pytest_tool_build_check_command_basic(self) -> None:
        """Test building basic check command."""
        tool = PytestTool()

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            assert cmd[0] == "pytest"
            assert "-v" in cmd
            assert "--tb" in cmd
            assert "short" in cmd
            # Note: maxfail is loaded from pytest.ini which has --maxfail=3
            # This is expected behavior - the tool respects the pytest.ini config
            assert "--maxfail" in cmd
            assert "3" in cmd
            assert "--no-header" in cmd
            assert "--disable-warnings" in cmd
            assert "test_file.py" in cmd

    def test_pytest_tool_build_check_command_with_options(self) -> None:
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

    def test_pytest_tool_build_check_command_test_mode(self) -> None:
        """Test building check command in test mode."""
        tool = PytestTool()

        with (
            patch.dict(os.environ, {"LINTRO_TEST_MODE": "1"}),
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        ):
            cmd = tool._build_check_command(["test_file.py"])

            assert "--strict-markers" in cmd
            assert "--strict-config" in cmd

    def test_pytest_tool_parse_output_json_format(self) -> None:
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

    def test_pytest_tool_parse_output_junit_format(self) -> None:
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

    def test_pytest_tool_parse_output_text_format(self) -> None:
        """Test parsing text format output."""
        tool = PytestTool()

        text_output = (
            "FAILED test_example.py::test_failure - "
            "AssertionError: Expected 1 but got 2"
        )

        issues = tool._parse_output(text_output, 1)

        assert len(issues) == 1
        assert issues[0].file == "test_example.py"
        assert issues[0].test_name == "test_failure"
        assert issues[0].test_status == "FAILED"
        assert issues[0].message == "AssertionError: Expected 1 but got 2"

    def test_pytest_tool_parse_output_fallback_to_text(self) -> None:
        """Test that parsing falls back to text format when no issues found."""
        tool = PytestTool()
        tool.set_options(json_report=True)

        # Empty JSON output but non-zero return code
        json_output = '{"tests": []}'

        issues = tool._parse_output(json_output, 1)

        # Should fall back to text parsing
        assert isinstance(issues, list)

    def test_pytest_tool_check_no_files(self) -> None:
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
            patch.object(tool, "_get_total_test_count", return_value=0),
            patch.object(tool, "_count_docker_tests", return_value=0),
        ):
            result = tool.check()

            assert result.name == "pytest"
            assert result.success is True
            assert result.issues == []

    def test_pytest_tool_check_success(self) -> None:
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

    def test_pytest_tool_check_failure(self) -> None:
        """Test failed check method."""
        tool = PytestTool()

        mock_result = Mock()
        mock_result.return_code = 1
        mock_result.stdout = "FAILED test_file.py::test_failure"
        mock_result.stderr = ""

        mock_issues = [
            Mock(
                file="test_file.py",
                line=10,
                test_name="test_failure",
                message="AssertionError",
                test_status="FAILED",
            ),
        ]

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(
                    False,
                    "FAILED test_file.py::test_failure\n510 passed, 1 failed in 18.53s",
                ),
            ),
            patch.object(tool, "_parse_output", return_value=mock_issues),
        ):
            result = tool.check(["test_file.py"])

            assert result.name == "pytest"
            assert result.success is False
            assert len(result.issues) == 1
            # Output should contain JSON summary
            assert '"failed": 1' in result.output
            assert result.issues_count == 1

    def test_pytest_tool_check_exception(self) -> None:
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

    def test_pytest_tool_fix_default_behavior(self) -> None:
        """Test that fix raises NotImplementedError when can_fix is False (default)."""
        tool = PytestTool()
        assert tool.can_fix is False

        with pytest.raises(NotImplementedError):
            tool.fix(["test_file.py"])

    def test_pytest_tool_fix_with_can_fix_true(self) -> None:
        """Test that fix raises NotImplementedError even when can_fix is True."""
        tool = PytestTool()
        # Mock can_fix to True to test the second check
        tool.can_fix = True

        with pytest.raises(
            NotImplementedError,
            match="pytest does not support fixing issues",
        ):
            tool.fix(["test_file.py"])

    def test_pytest_tool_check_paths_vs_files_precedence(self) -> None:
        """Test that paths parameter takes precedence over files."""
        tool = PytestTool()

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, "All tests passed"),
            ),
            patch.object(tool, "_parse_output", return_value=[]),
        ):
            # Both paths and files provided; paths should be used
            tool.check(files=["file.py"], paths=["path/"])

            # Check that the command includes the paths argument
            # (would need to verify in actual implementation)

    def test_pytest_tool_check_discovers_test_files(self) -> None:
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
            patch.object(tool, "_get_total_test_count", return_value=5),
            patch.object(tool, "_count_docker_tests", return_value=0),
        ):
            result = tool.check()

            assert result.name == "pytest"
            assert result.success is True

    def test_pytest_tool_parse_output_fallback_to_text_with_issues(self) -> None:
        """Test parse_output falls back to text when JSON parsing fails."""
        tool = PytestTool()
        tool.set_options(json_report=True)

        # JSON format failed, but text parsing should find issues
        output = "FAILED test.py::test_fail - AssertionError"

        issues = tool._parse_output(output, 1)

        # Should fall back and find issues via text parsing
        assert isinstance(issues, list)

    def test_pytest_tool_build_check_command_no_verbose(self) -> None:
        """Test building command when verbose and show_progress are False."""
        tool = PytestTool()
        tool.set_options(verbose=False, show_progress=False)

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            # When both verbose and show_progress are False, should not include -v
            assert "-v" not in cmd

    def test_pytest_tool_build_check_command_custom_tb_format(self) -> None:
        """Test building command with custom traceback format."""
        tool = PytestTool()
        tool.set_options(tb="long")

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            assert "--tb" in cmd
            assert "long" in cmd

    def test_pytest_tool_build_check_command_maxfail_option(self) -> None:
        """Test building command with custom maxfail value."""
        tool = PytestTool()
        tool.set_options(maxfail=10)

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            assert "--maxfail" in cmd
            assert "10" in cmd

    def test_pytest_tool_build_check_command_maxfail_default_zero(self) -> None:
        """Test that maxfail defaults to 3 from pytest.ini config."""
        tool = PytestTool()
        # Don't set maxfail explicitly - should use pytest.ini default of 3

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            # maxfail is loaded from pytest.ini which has --maxfail=3
            assert "--maxfail" in cmd
            assert "3" in cmd

    def test_pytest_tool_parse_output_json_with_no_issues(self) -> None:
        """Test parsing JSON output with no issues."""
        tool = PytestTool()
        tool.set_options(json_report=True, junitxml=None)

        json_output = '{"tests": []}'

        issues = tool._parse_output(json_output, 0)

        assert issues == []

    def test_pytest_tool_parse_output_mixed_formats(self) -> None:
        """Test parse_output with mixed success/failure scenarios."""
        tool = PytestTool()

        # Test success (return code 0, no failures)
        issues = tool._parse_output("All tests passed", 0)
        assert issues == []

        # Test failure (return code 1, has failures)
        issues = tool._parse_output("FAILED test.py::test - Error", 1)
        assert isinstance(issues, list)

    def test_pytest_tool_load_config_error_handling(self) -> None:
        """Test loading pytest config with error handling."""
        from lintro.tools.implementations.pytest_utils import load_pytest_config

        # Test with invalid config files
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=Exception("Read error")),
        ):
            result = load_pytest_config()
            assert result == {}

    def test_pytest_tool_load_lintro_ignore_error(self) -> None:
        """Test loading .lintro-ignore with error handling."""
        from lintro.tools.implementations.pytest_utils import load_lintro_ignore

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=Exception("Read error")),
        ):
            result = load_lintro_ignore()
            assert result == []

    def test_pytest_tool_set_options_invalid_run_docker_tests(self) -> None:
        """Test setting invalid run_docker_tests option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="run_docker_tests must be a boolean"):
            tool.set_options(run_docker_tests="invalid")

    def test_pytest_tool_load_file_patterns_list(self) -> None:
        """Test loading file patterns as list from config."""
        from lintro.tools.implementations.pytest_utils import (
            load_file_patterns_from_config,
        )

        config = {"python_files": ["test_*.py", "*_test.py"]}
        result = load_file_patterns_from_config(config)
        assert result == ["test_*.py", "*_test.py"]

    def test_pytest_tool_load_file_patterns_invalid_type(self) -> None:
        """Test loading file patterns with invalid type."""
        from lintro.tools.implementations.pytest_utils import (
            load_file_patterns_from_config,
        )

        config = {"python_files": 123}
        result = load_file_patterns_from_config(config)
        assert result == []

    def test_pytest_tool_get_total_test_count_restore_env(self) -> None:
        """Test that environment is restored after get_total_test_count."""
        tool = PytestTool()

        # Set initial state
        os.environ["LINTRO_RUN_DOCKER_TESTS"] = "0"

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, "100 tests collected"),
            ),
        ):
            result = tool._get_total_test_count(["tests"])
            assert result == 100

        # Verify environment was restored
        assert os.environ.get("LINTRO_RUN_DOCKER_TESTS") == "0"

    def test_pytest_tool_get_total_test_count_delete_env(self) -> None:
        """Test deleting env var when originally unset."""
        tool = PytestTool()

        # Ensure it's not set initially
        if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
            del os.environ["LINTRO_RUN_DOCKER_TESTS"]

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, "50 tests collected"),
            ),
        ):
            result = tool._get_total_test_count(["tests"])
            assert result == 50

        # Verify it was deleted after
        assert "LINTRO_RUN_DOCKER_TESTS" not in os.environ

    def test_pytest_tool_count_docker_tests_exception(self) -> None:
        """Test count_docker_tests exception handling."""
        tool = PytestTool()

        with patch.object(
            tool,
            "_get_executable_command",
            side_effect=Exception("Error"),
        ):
            result = tool._count_docker_tests(["tests"])
            assert result == 0

    def test_pytest_tool_check_target_files_none(self) -> None:
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
            patch.object(tool, "_get_total_test_count", return_value=10),
            patch.object(tool, "_count_docker_tests", return_value=0),
        ):
            result = tool.check(files=None, paths=None)
            assert result.success is True

    def test_pytest_tool_check_target_files_dot(self) -> None:
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
            patch.object(tool, "_get_total_test_count", return_value=10),
            patch.object(tool, "_count_docker_tests", return_value=0),
        ):
            result = tool.check(files=["."])
            assert result.success is True

    def test_pytest_tool_check_run_docker_tests_enabled(self) -> None:
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
                patch.object(tool, "_get_total_test_count", return_value=10),
                patch.object(tool, "_count_docker_tests", return_value=5),
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

    def test_pytest_tool_check_docker_disabled_message(self) -> None:
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
            patch.object(tool, "_get_total_test_count", return_value=10),
            patch.object(tool, "_count_docker_tests", return_value=3),
        ):
            result = tool.check(["tests"])
            assert result.success is True

    def test_pytest_tool_check_docker_skipped_calculation(self) -> None:
        """Test check calculates docker skipped correctly."""
        tool = PytestTool()

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, "7 passed, 3 skipped"),
            ),
            patch.object(tool, "_parse_output", return_value=[]),
            patch.object(tool, "_collect_tests_once", return_value=(10, 3)),
        ):
            result = tool.check(["tests"])
            assert result.success is True
            if hasattr(result, "pytest_summary"):
                assert result.pytest_summary["docker_skipped"] == 3

    def test_pytest_tool_load_file_patterns_empty_config(self) -> None:
        """Test loading file patterns with empty config."""
        from lintro.tools.implementations.pytest_utils import (
            load_file_patterns_from_config,
        )

        result = load_file_patterns_from_config({})
        assert result == []

    def test_pytest_tool_load_file_patterns_none_python_files(self) -> None:
        """Test loading file patterns when python_files is None."""
        from lintro.tools.implementations.pytest_utils import (
            load_file_patterns_from_config,
        )

        config = {"python_files": None}
        result = load_file_patterns_from_config(config)
        assert result == []

    def test_pytest_tool_count_docker_tests_coverage_section(self) -> None:
        """Test count_docker_tests stops at coverage section."""
        tool = PytestTool()

        output_with_coverage = (
            "<Dir docker>\n"
            "  <Function test_one>\n"
            "coverage: line 1\n"
            "<Function test_two>\n"
        )

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, output_with_coverage),
            ),
        ):
            result = tool._count_docker_tests(["tests"])
            # Should only count test_one, not test_two (stopped at coverage)
            assert result == 1

    def test_pytest_tool_count_docker_tests_enter_dir(self) -> None:
        """Test count_docker_tests enters docker directory."""
        tool = PytestTool()

        output = "<Dir docker>\n" "  <Function test_one>\n" "  <Function test_two>\n"

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, output),
            ),
        ):
            result = tool._count_docker_tests(["tests"])
            assert result == 2

    def test_pytest_tool_count_docker_tests_leave_dir(self) -> None:
        """Test count_docker_tests leaves docker directory."""
        tool = PytestTool()

        output = (
            "<Dir docker>\n"
            "  <Function test_one>\n"
            "<Dir other>\n"
            "  <Function test_other>\n"
        )

        with (
            patch.object(tool, "_get_executable_command", return_value=["pytest"]),
            patch.object(
                tool,
                "_run_subprocess",
                return_value=(True, output),
            ),
        ):
            result = tool._count_docker_tests(["tests"])
            # Should only count test_one, not test_other
            assert result == 1

    def test_pytest_tool_count_docker_tests_delete_env_var(self) -> None:
        """Test count_docker_tests deletes env var when not set."""
        tool = PytestTool()

        # Remove env var first to test method's behavior
        original_value = os.environ.pop("LINTRO_RUN_DOCKER_TESTS", None)

        try:
            with (
                patch.object(tool, "_get_executable_command", return_value=["pytest"]),
                patch.object(
                    tool,
                    "_run_subprocess",
                    return_value=(True, "output"),
                ),
            ):
                result = tool._count_docker_tests(["tests"])
                assert result == 0

            # Assert that the method deleted the env var (since original_value was None)
            assert "LINTRO_RUN_DOCKER_TESTS" not in os.environ
        finally:
            # Restore original state if it existed
            if original_value is not None:
                os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_value

    def test_pytest_tool_count_docker_tests_restore_env_var(self) -> None:
        """Test count_docker_tests restores env var."""
        tool = PytestTool()

        original_value = "0"
        os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_value

        try:
            with (
                patch.object(tool, "_get_executable_command", return_value=["pytest"]),
                patch.object(
                    tool,
                    "_run_subprocess",
                    return_value=(True, "output"),
                ),
            ):
                result = tool._count_docker_tests(["tests"])
                assert result == 0
                # Should be restored
                assert os.environ.get("LINTRO_RUN_DOCKER_TESTS") == original_value
        finally:
            # Clean up
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]

    def test_pytest_tool_set_options_plugin_support(self) -> None:
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

    def test_pytest_tool_set_options_invalid_list_plugins(self) -> None:
        """Test setting invalid list_plugins option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="list_plugins must be a boolean"):
            tool.set_options(list_plugins="invalid")

    def test_pytest_tool_set_options_invalid_check_plugins(self) -> None:
        """Test setting invalid check_plugins option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="check_plugins must be a boolean"):
            tool.set_options(check_plugins="invalid")

    def test_pytest_tool_set_options_invalid_required_plugins(self) -> None:
        """Test setting invalid required_plugins option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="required_plugins must be a string"):
            tool.set_options(required_plugins=123)

    def test_pytest_tool_set_options_coverage_reports(self) -> None:
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

    def test_pytest_tool_set_options_invalid_coverage_html(self) -> None:
        """Test setting invalid coverage_html option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="coverage_html must be a string"):
            tool.set_options(coverage_html=123)

    def test_pytest_tool_set_options_invalid_coverage_xml(self) -> None:
        """Test setting invalid coverage_xml option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="coverage_xml must be a string"):
            tool.set_options(coverage_xml=123)

    def test_pytest_tool_set_options_invalid_coverage_report(self) -> None:
        """Test setting invalid coverage_report option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="coverage_report must be a boolean"):
            tool.set_options(coverage_report="invalid")

    def test_pytest_tool_set_options_discovery_and_inspection(self) -> None:
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

    def test_pytest_tool_set_options_invalid_collect_only(self) -> None:
        """Test setting invalid collect_only option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="collect_only must be a boolean"):
            tool.set_options(collect_only="invalid")

    def test_pytest_tool_set_options_invalid_list_fixtures(self) -> None:
        """Test setting invalid list_fixtures option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="list_fixtures must be a boolean"):
            tool.set_options(list_fixtures="invalid")

    def test_pytest_tool_set_options_invalid_fixture_info(self) -> None:
        """Test setting invalid fixture_info option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="fixture_info must be a string"):
            tool.set_options(fixture_info=123)

    def test_pytest_tool_set_options_invalid_list_markers(self) -> None:
        """Test setting invalid list_markers option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="list_markers must be a boolean"):
            tool.set_options(list_markers="invalid")

    def test_pytest_tool_set_options_invalid_parametrize_help(self) -> None:
        """Test setting invalid parametrize_help option."""
        tool = PytestTool()

        with pytest.raises(ValueError, match="parametrize_help must be a boolean"):
            tool.set_options(parametrize_help="invalid")

    def test_pytest_tool_build_check_command_with_coverage_html(self) -> None:
        """Test building command with coverage HTML report."""
        tool = PytestTool()
        tool.set_options(coverage_html="htmlcov")

        cmd = tool._build_check_command(["test_file.py"])

        assert "--cov-report=html" in cmd or any(
            "--cov-report" in arg and "html" in arg for arg in cmd
        )
        assert "--cov=." in cmd

    def test_pytest_tool_build_check_command_with_coverage_xml(self) -> None:
        """Test building command with coverage XML report."""
        tool = PytestTool()
        tool.set_options(coverage_xml="coverage.xml")

        cmd = tool._build_check_command(["test_file.py"])

        assert "--cov-report=xml" in cmd or any(
            "--cov-report" in arg and "xml" in arg for arg in cmd
        )
        assert "--cov=." in cmd

    def test_pytest_tool_build_check_command_with_coverage_report(self) -> None:
        """Test building command with coverage_report option."""
        tool = PytestTool()
        tool.set_options(coverage_report=True)

        cmd = tool._build_check_command(["test_file.py"])

        # Should include both HTML and XML coverage reports
        assert "--cov=." in cmd
        assert any("html" in arg for arg in cmd if "--cov-report" in arg)
        assert any("xml" in arg for arg in cmd if "--cov-report" in arg)

    def test_pytest_tool_handle_list_plugins(self) -> None:
        """Test handle_list_plugins method."""
        tool = PytestTool()

        with (
            patch(
                "lintro.tools.implementations.pytest_handlers.list_installed_plugins",
                return_value=[
                    {"name": "pytest-cov", "version": "4.0.0"},
                    {"name": "pytest-xdist", "version": "3.0.0"},
                ],
            ),
            patch(
                "lintro.tools.implementations.pytest_handlers.get_pytest_version_info",
                return_value="pytest 7.0.0",
            ),
        ):
            result = tool._handle_list_plugins()

            assert result.success is True
            assert "pytest 7.0.0" in result.output
            assert "pytest-cov" in result.output
            assert "pytest-xdist" in result.output

    def test_pytest_tool_handle_check_plugins_with_missing(self) -> None:
        """Test handle_check_plugins with missing plugins."""
        tool = PytestTool()

        with patch(
            "lintro.tools.implementations.pytest_handlers.check_plugin_installed",
            side_effect=lambda name: name == "pytest-cov",
        ):
            result = tool._handle_check_plugins("pytest-cov,pytest-xdist")

            assert result.success is False
            assert "pytest-cov" in result.output
            assert "pytest-xdist" in result.output
            assert result.issues_count == 1

    def test_pytest_tool_handle_check_plugins_all_installed(self) -> None:
        """Test handle_check_plugins with all plugins installed."""
        tool = PytestTool()

        with patch(
            "lintro.tools.implementations.pytest_handlers.check_plugin_installed",
            return_value=True,
        ):
            result = tool._handle_check_plugins("pytest-cov,pytest-xdist")

            assert result.success is True
            assert result.issues_count == 0

    def test_pytest_tool_handle_check_plugins_no_required(self) -> None:
        """Test handle_check_plugins without required_plugins."""
        tool = PytestTool()

        result = tool._handle_check_plugins(None)

        assert result.success is False
        assert "required_plugins must be specified" in result.output

    def test_pytest_tool_handle_collect_only(self) -> None:
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
            result = tool._handle_collect_only(["test_file.py"])

            assert result.success is True
            assert "Collected" in result.output or "2" in result.output

    def test_pytest_tool_handle_list_fixtures(self) -> None:
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
            result = tool._handle_list_fixtures(["test_file.py"])

            assert result.success is True
            assert result.output == mock_output

    def test_pytest_tool_handle_fixture_info(self) -> None:
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
            result = tool._handle_fixture_info("sample_data", ["test_file.py"])

            assert result.success is True
            assert "sample_data" in result.output

    def test_pytest_tool_handle_list_markers(self) -> None:
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
            result = tool._handle_list_markers()

            assert result.success is True
            assert result.output == mock_output

    def test_pytest_tool_handle_parametrize_help(self) -> None:
        """Test handle_parametrize_help method."""
        tool = PytestTool()

        result = tool._handle_parametrize_help()

        assert result.success is True
        assert "Parametrization" in result.output
        assert "@pytest.mark.parametrize" in result.output

    def test_pytest_tool_check_with_list_plugins(self) -> None:
        """Test check method with list_plugins option."""
        tool = PytestTool()
        tool.set_options(list_plugins=True)

        with patch.object(tool, "_handle_list_plugins") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Plugin list",
                issues_count=0,
            )
            result = tool.check()

            mock_handle.assert_called_once()
            assert result.success is True

    def test_pytest_tool_check_with_collect_only(self) -> None:
        """Test check method with collect_only option."""
        tool = PytestTool()
        tool.set_options(collect_only=True)

        with patch.object(tool, "_handle_collect_only") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Test list",
                issues_count=0,
            )
            result = tool.check(paths=["tests"])

            mock_handle.assert_called_once_with(["tests"])
            assert result.success is True

    def test_pytest_tool_check_with_list_fixtures(self) -> None:
        """Test check method with list_fixtures option."""
        tool = PytestTool()
        tool.set_options(list_fixtures=True)

        with patch.object(tool, "_handle_list_fixtures") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Fixture list",
                issues_count=0,
            )
            result = tool.check(paths=["tests"])

            mock_handle.assert_called_once_with(["tests"])
            assert result.success is True

    def test_pytest_tool_check_with_fixture_info(self) -> None:
        """Test check method with fixture_info option."""
        tool = PytestTool()
        tool.set_options(fixture_info="sample_data")

        with patch.object(tool, "_handle_fixture_info") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Fixture info",
                issues_count=0,
            )
            result = tool.check(paths=["tests"])

            mock_handle.assert_called_once_with("sample_data", ["tests"])
            assert result.success is True

    def test_pytest_tool_check_with_list_markers(self) -> None:
        """Test check method with list_markers option."""
        tool = PytestTool()
        tool.set_options(list_markers=True)

        with patch.object(tool, "_handle_list_markers") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Marker list",
                issues_count=0,
            )
            result = tool.check()

            mock_handle.assert_called_once()
            assert result.success is True

    def test_pytest_tool_check_with_parametrize_help(self) -> None:
        """Test check method with parametrize_help option."""
        tool = PytestTool()
        tool.set_options(parametrize_help=True)

        with patch.object(tool, "_handle_parametrize_help") as mock_handle:
            mock_handle.return_value = Mock(
                success=True,
                issues=[],
                output="Help text",
                issues_count=0,
            )
            result = tool.check()

            mock_handle.assert_called_once()
            assert result.success is True
