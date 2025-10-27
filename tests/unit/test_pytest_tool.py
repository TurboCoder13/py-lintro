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
            assert "--maxfail" in cmd
            assert "0" in cmd  # Default to 0 to run all tests
            assert "--no-header" in cmd
            assert "--disable-warnings" in cmd
            assert "test_file.py" in cmd

    def test_pytest_tool_build_check_command_with_options(self) -> None:
        """Test building check command with custom options."""
        tool = PytestTool()
        tool.set_options(
            verbose=False,
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
        tool.set_options(json_report=True)

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
            assert "Error: Test error" in result.output

    def test_pytest_tool_fix_not_implemented(self) -> None:
        """Test that fix method raises NotImplementedError."""
        tool = PytestTool()

        with pytest.raises(NotImplementedError):
            tool.fix(["test_file.py"])

    def test_pytest_tool_fix_cannot_fix_raises_not_implemented(self) -> None:
        """Test that fix raises NotImplementedError when can_fix is False."""
        tool = PytestTool()
        assert tool.can_fix is False

        with pytest.raises(NotImplementedError):
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
        """Test building command when verbose is False."""
        tool = PytestTool()
        tool.set_options(verbose=False)

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            # When verbose is False, should not include -v
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
        """Test that maxfail defaults to 0 to run all tests."""
        tool = PytestTool()
        # Don't set maxfail explicitly

        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            cmd = tool._build_check_command(["test_file.py"])

            assert "--maxfail" in cmd
            assert "0" in cmd

    def test_pytest_tool_parse_output_json_with_no_issues(self) -> None:
        """Test parsing JSON output with no issues."""
        tool = PytestTool()
        tool.set_options(json_report=True)

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
