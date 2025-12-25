"""Unit tests for pytest tool output parsing functionality."""

from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


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

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test_example.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].test_name).is_equal_to("test_failure")
    assert_that(issues[0].test_status).is_equal_to("FAILED")
    assert_that(issues[0].message).is_equal_to("AssertionError: Expected 1 but got 2")


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

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test_example.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].test_name).is_equal_to("test_failure")
    assert_that(issues[0].test_status).is_equal_to("FAILED")


def test_pytest_tool_parse_output_text_format() -> None:
    """Test parsing text format output."""
    tool = PytestTool()

    text_output = (
        "FAILED test_example.py::test_failure - AssertionError: Expected 1 but got 2"
    )

    issues = tool._parse_output(text_output, 1)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test_example.py")
    assert_that(issues[0].test_name).is_equal_to("test_failure")
    assert_that(issues[0].test_status).is_equal_to("FAILED")
    assert_that(issues[0].message).is_equal_to("AssertionError: Expected 1 but got 2")


def test_pytest_tool_parse_output_fallback_to_text() -> None:
    """Test that parsing falls back to text format when no issues found."""
    tool = PytestTool()
    tool.set_options(json_report=True)

    # Empty JSON output but non-zero return code
    json_output = '{"tests": []}'

    issues = tool._parse_output(json_output, 1)

    # Should fall back to text parsing
    assert_that(issues).is_instance_of(list)


def test_pytest_tool_parse_output_fallback_to_text_with_issues() -> None:
    """Test parse_output falls back to text when JSON parsing fails."""
    tool = PytestTool()
    tool.set_options(json_report=True)

    # JSON format failed, but text parsing should find issues
    output = "FAILED test.py::test_fail - AssertionError"

    issues = tool._parse_output(output, 1)

    # Should fall back and find issues via text parsing
    assert_that(issues).is_instance_of(list)


def test_pytest_tool_parse_output_json_with_no_issues() -> None:
    """Test parsing JSON output with no issues."""
    tool = PytestTool()
    tool.set_options(json_report=True, junitxml=None)

    json_output = '{"tests": []}'

    issues = tool._parse_output(json_output, 0)

    assert_that(issues).is_empty()


def test_pytest_tool_parse_output_mixed_formats() -> None:
    """Test parse_output with mixed success/failure scenarios."""
    tool = PytestTool()

    # Test success (return code 0, no failures)
    issues = tool._parse_output("All tests passed", 0)
    assert_that(issues).is_empty()

    # Test failure (return code 1, has failures)
    issues = tool._parse_output("FAILED test.py::test - Error", 1)
    assert_that(issues).is_instance_of(list)
