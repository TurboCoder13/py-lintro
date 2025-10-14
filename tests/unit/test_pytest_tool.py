"""Unit tests for pytest tool implementation."""

import os
from unittest.mock import Mock, patch

import pytest

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.tools.implementations.tool_pytest import PytestTool


class TestPytestTool:
    """Test cases for PytestTool class."""

    def test_pytest_tool_initialization(self) -> None:
        """Test that PytestTool initializes correctly."""
        tool = PytestTool()
        
        assert tool.name == "pytest"
        assert "Python testing tool" in tool.description
        assert tool.can_fix is False
        assert tool.config.tool_type == ToolType.LINTER
        assert tool._default_timeout == 300
        assert tool.config.priority == 90
        assert "test_*.py" in tool.config.file_patterns
        assert "*_test.py" in tool.config.file_patterns

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
            assert "1" in cmd
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
        
        with patch.dict(os.environ, {"LINTRO_TEST_MODE": "1"}):
            with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
                cmd = tool._build_check_command(["test_file.py"])
                
                assert "--strict-markers" in cmd
                assert "--strict-config" in cmd

    def test_pytest_tool_parse_output_json_format(self) -> None:
        """Test parsing JSON format output."""
        tool = PytestTool()
        tool.set_options(json_report=True)
        
        json_output = '''{
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
        }'''
        
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
        
        xml_output = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="1" errors="0" time="0.001">
    <testcase name="test_failure" file="test_example.py" line="10" time="0.001" classname="TestExample">
        <failure message="AssertionError: Expected 1 but got 2">Traceback...</failure>
    </testcase>
</testsuite>"""
        
        issues = tool._parse_output(xml_output, 1)
        
        assert len(issues) == 1
        assert issues[0].file == "test_example.py"
        assert issues[0].line == 10
        assert issues[0].test_name == "test_failure"
        assert issues[0].test_status == "FAILED"

    def test_pytest_tool_parse_output_text_format(self) -> None:
        """Test parsing text format output."""
        tool = PytestTool()
        
        text_output = "FAILED test_example.py::test_failure - AssertionError: Expected 1 but got 2"
        
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
        
        # Mock the walk_files_with_excludes function to return empty list
        with patch("lintro.tools.implementations.tool_pytest.walk_files_with_excludes", return_value=[]):
            result = tool.check()
            
            assert result.name == "pytest"
            assert result.success is True
            assert result.issues == []
            assert "No test files found" in result.output

    def test_pytest_tool_check_success(self) -> None:
        """Test successful check method."""
        tool = PytestTool()
        
        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""
        
        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            with patch.object(tool, "_run_subprocess", return_value=(True, "All tests passed")):
                with patch.object(tool, "_parse_output", return_value=[]):
                    result = tool.check(["test_file.py"])
                    
                    assert result.name == "pytest"
                    assert result.success is True
                    assert result.issues == []
                    assert result.output == "All tests passed"

    def test_pytest_tool_check_failure(self) -> None:
        """Test failed check method."""
        tool = PytestTool()
        
        mock_result = Mock()
        mock_result.return_code = 1
        mock_result.stdout = "FAILED test_file.py::test_failure"
        mock_result.stderr = ""
        
        mock_issues = [
            Mock(file="test_file.py", line=10, test_name="test_failure", 
                 message="AssertionError", test_status="FAILED")
        ]
        
        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            with patch.object(tool, "_run_subprocess", return_value=(False, "FAILED test_file.py::test_failure")):
                with patch.object(tool, "_parse_output", return_value=mock_issues):
                    result = tool.check(["test_file.py"])
                    
                    assert result.name == "pytest"
                    assert result.success is False
                    assert len(result.issues) == 1
                    assert result.output == "FAILED test_file.py::test_failure"

    def test_pytest_tool_check_exception(self) -> None:
        """Test check method with exception."""
        tool = PytestTool()
        
        with patch.object(tool, "_get_executable_command", return_value=["pytest"]):
            with patch.object(tool, "_run_subprocess", side_effect=Exception("Test error")):
                result = tool.check(["test_file.py"])
                
                assert result.name == "pytest"
                assert result.success is False
                assert result.issues == []
                assert "Error: Test error" in result.output
