"""Unit tests for pytest parser."""

from lintro.parsers.pytest.pytest_parser import (
    parse_pytest_json_output,
    parse_pytest_junit_xml,
    parse_pytest_output,
    parse_pytest_text_output,
)


class TestPytestParser:
    """Test cases for pytest parser functions."""

    def test_parse_pytest_json_output_empty(self) -> None:
        """Test parsing empty JSON output."""
        result = parse_pytest_json_output("")
        assert result == []

        result = parse_pytest_json_output("{}")
        assert result == []

        result = parse_pytest_json_output("[]")
        assert result == []

    def test_parse_pytest_json_output_valid(self) -> None:
        """Test parsing valid JSON output."""
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
                },
                {
                    "file": "test_example.py",
                    "lineno": 15,
                    "name": "test_error",
                    "outcome": "error",
                    "longrepr": "ZeroDivisionError: division by zero",
                    "duration": 0.002,
                    "nodeid": "test_example.py::test_error"
                }
            ]
        }"""

        result = parse_pytest_json_output(json_output)
        assert len(result) == 2

        assert result[0].file == "test_example.py"
        assert result[0].line == 10
        assert result[0].test_name == "test_failure"
        assert result[0].test_status == "FAILED"
        assert result[0].message == "AssertionError: Expected 1 but got 2"
        assert result[0].duration == 0.001
        assert result[0].node_id == "test_example.py::test_failure"

        assert result[1].file == "test_example.py"
        assert result[1].line == 15
        assert result[1].test_name == "test_error"
        assert result[1].test_status == "ERROR"
        assert result[1].message == "ZeroDivisionError: division by zero"
        assert result[1].duration == 0.002
        assert result[1].node_id == "test_example.py::test_error"

    def test_parse_pytest_text_output_empty(self) -> None:
        """Test parsing empty text output."""
        result = parse_pytest_text_output("")
        assert result == []

    def test_parse_pytest_text_output_failures(self) -> None:
        """Test parsing text output with failures."""
        text_output = (
            "FAILED test_example.py::test_failure - "
            "AssertionError: Expected 1 but got 2\n"
            "ERROR test_example.py::test_error - "
            "ZeroDivisionError: division by zero\n"
            "FAILED test_example.py::test_another_failure - "
            "ValueError: invalid value\n"
        )

        result = parse_pytest_text_output(text_output)
        assert len(result) == 3

        assert result[0].file == "test_example.py"
        assert result[0].test_name == "test_failure"
        assert result[0].test_status == "FAILED"
        assert result[0].message == "AssertionError: Expected 1 but got 2"

        assert result[1].file == "test_example.py"
        assert result[1].test_name == "test_error"
        assert result[1].test_status == "ERROR"
        assert result[1].message == "ZeroDivisionError: division by zero"

        assert result[2].file == "test_example.py"
        assert result[2].test_name == "test_another_failure"
        assert result[2].test_status == "FAILED"
        assert result[2].message == "ValueError: invalid value"

    def test_parse_pytest_text_output_line_format(self) -> None:
        """Test parsing text output with line number format."""
        text_output = (
            "test_example.py:10: FAILED - AssertionError: Expected 1 but got 2\n"
            "test_example.py:15: ERROR - ZeroDivisionError: division by zero\n"
        )

        result = parse_pytest_text_output(text_output)
        assert len(result) == 2

        assert result[0].file == "test_example.py"
        assert result[0].line == 10
        assert result[0].test_status == "FAILED"
        assert result[0].message == "AssertionError: Expected 1 but got 2"

        assert result[1].file == "test_example.py"
        assert result[1].line == 15
        assert result[1].test_status == "ERROR"
        assert result[1].message == "ZeroDivisionError: division by zero"

    def test_parse_pytest_junit_xml_empty(self) -> None:
        """Test parsing empty JUnit XML output."""
        result = parse_pytest_junit_xml("")
        assert result == []

    def test_parse_pytest_junit_xml_valid(self) -> None:
        """Test parsing valid JUnit XML output."""
        xml_output = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<testsuite name="pytest" tests="2" failures="1" errors="1" time="0.003">\n'
            '    <testcase name="test_failure" file="test_example.py" line="10" '
            'time="0.001" classname="TestExample">\n'
            '        <failure message="AssertionError: Expected 1 but got 2">'
            "Traceback (most recent call last):\n"
            '  File "test_example.py", line 10, in test_failure\n'
            "    assert 1 == 2\n"
            "AssertionError: Expected 1 but got 2</failure>\n"
            "    </testcase>\n"
            '    <testcase name="test_error" file="test_example.py" line="15" '
            'time="0.002" classname="TestExample">\n'
            '        <error message="ZeroDivisionError: division by zero">'
            "Traceback (most recent call last):\n"
            '  File "test_example.py", line 15, in test_error\n'
            "    1 / 0\n"
            "ZeroDivisionError: division by zero</error>\n"
            "    </testcase>\n"
            "</testsuite>"
        )

        result = parse_pytest_junit_xml(xml_output)
        assert len(result) == 2

        assert result[0].file == "test_example.py"
        assert result[0].line == 10
        assert result[0].test_name == "test_failure"
        assert result[0].test_status == "FAILED"
        assert "AssertionError: Expected 1 but got 2" in result[0].message
        assert result[0].duration == 0.001
        assert result[0].node_id == "TestExample::test_failure"

        assert result[1].file == "test_example.py"
        assert result[1].line == 15
        assert result[1].test_name == "test_error"
        assert result[1].test_status == "ERROR"
        assert "ZeroDivisionError: division by zero" in result[1].message
        assert result[1].duration == 0.002
        assert result[1].node_id == "TestExample::test_error"

    def test_parse_pytest_output_format_dispatch(self) -> None:
        """Test that parse_pytest_output dispatches to correct parser."""
        # Test JSON format
        json_output = '{"tests": []}'
        result = parse_pytest_output(json_output, format="json")
        assert isinstance(result, list)

        # Test text format
        text_output = "FAILED test.py::test - AssertionError"
        result = parse_pytest_output(text_output, format="text")
        assert isinstance(result, list)

        # Test junit format
        xml_output = '<?xml version="1.0"?><testsuite></testsuite>'
        result = parse_pytest_output(xml_output, format="junit")
        assert isinstance(result, list)

        # Test default format (text)
        result = parse_pytest_output(text_output)
        assert isinstance(result, list)

    def test_parse_pytest_json_output_malformed(self) -> None:
        """Test parsing malformed JSON output."""
        malformed_json = '{"tests": [{"incomplete": "object"'
        result = parse_pytest_json_output(malformed_json)
        assert result == []

    def test_parse_pytest_junit_xml_malformed(self) -> None:
        """Test parsing malformed JUnit XML output."""
        malformed_xml = "<testsuite><testcase><incomplete>"
        result = parse_pytest_junit_xml(malformed_xml)
        assert result == []

    def test_parse_pytest_text_output_ansi_codes(self) -> None:
        """Test parsing text output with ANSI color codes."""
        text_with_ansi = (
            "\x1b[31mFAILED\x1b[0m test_example.py::test_failure - AssertionError"
        )
        result = parse_pytest_text_output(text_with_ansi)
        assert len(result) == 1
        assert result[0].test_status == "FAILED"
        assert result[0].message == "AssertionError"

    def test_parse_pytest_json_output_missing_optional_fields(self) -> None:
        """Test parsing JSON with missing optional fields."""
        json_output = """{
            "tests": [
                {
                    "file": "test_example.py",
                    "name": "test_failure",
                    "outcome": "failed"
                }
            ]
        }"""
        result = parse_pytest_json_output(json_output)
        assert len(result) == 1
        assert result[0].file == "test_example.py"
        assert result[0].line == 0
        assert result[0].duration == 0.0

    def test_parse_pytest_json_output_alternative_list_format(self) -> None:
        """Test parsing JSON alternative list format."""
        json_output = """[
            {
                "file": "test_example.py",
                "name": "test_failure",
                "outcome": "failed",
                "longrepr": "AssertionError"
            }
        ]"""
        result = parse_pytest_json_output(json_output)
        assert len(result) == 1
        assert result[0].file == "test_example.py"

    def test_parse_pytest_json_output_with_call_message(self) -> None:
        """Test parsing JSON with message in call field."""
        json_output = """{
            "tests": [
                {
                    "file": "test_example.py",
                    "name": "test_failure",
                    "outcome": "failed",
                    "call": {
                        "longrepr": "Error in call"
                    },
                    "longrepr": "Error in test"
                }
            ]
        }"""
        result = parse_pytest_json_output(json_output)
        assert len(result) == 1
        # Should prefer call.longrepr
        assert result[0].message == "Error in call"

    def test_parse_pytest_json_output_passed_test_ignored(self) -> None:
        """Test that passed tests are ignored in JSON parsing."""
        json_output = """{
            "tests": [
                {
                    "file": "test_example.py",
                    "name": "test_success",
                    "outcome": "passed"
                },
                {
                    "file": "test_example.py",
                    "name": "test_failure",
                    "outcome": "failed",
                    "longrepr": "Error"
                }
            ]
        }"""
        result = parse_pytest_json_output(json_output)
        assert len(result) == 1
        assert result[0].test_name == "test_failure"

    def test_parse_pytest_text_output_alternative_failure_format(self) -> None:
        """Test parsing text output with alternative failure format."""
        text_output = "FAILED test_example.py::test_failure Some error message"
        result = parse_pytest_text_output(text_output)
        # Should parse using alternative pattern
        assert len(result) == 1
        assert result[0].file == "test_example.py"
        assert result[0].test_name == "test_failure"
        assert result[0].test_status == "FAILED"
        assert "Some error message" in result[0].message

    def test_parse_pytest_text_output_multiple_failures(self) -> None:
        """Test parsing text output with multiple failure types."""
        text_output = (
            "FAILED test_a.py::test_1 - Error 1\n"
            "ERROR test_b.py::test_2 - Error 2\n"
            "FAILED test_c.py::test_3 - Error 3\n"
        )
        result = parse_pytest_text_output(text_output)
        assert len(result) == 3

    def test_parse_pytest_junit_xml_missing_attributes(self) -> None:
        """Test parsing JUnit XML with missing attributes."""
        xml_output = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<testsuite>\n"
            '    <testcase name="test_failure">\n'
            '        <failure message="Error">Traceback</failure>\n'
            "    </testcase>\n"
            "</testsuite>"
        )
        result = parse_pytest_junit_xml(xml_output)
        assert len(result) == 1
        assert result[0].test_name == "test_failure"

    def test_parse_pytest_junit_xml_without_message_attribute(self) -> None:
        """Test parsing JUnit XML failure without message attribute."""
        xml_output = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<testsuite>\n"
            '    <testcase name="test_failure" file="test.py">\n'
            "        <failure>Error text content</failure>\n"
            "    </testcase>\n"
            "</testsuite>"
        )
        result = parse_pytest_junit_xml(xml_output)
        assert len(result) == 1
        assert "Error text content" in result[0].message

    def test_parse_pytest_junit_xml_no_failure_or_error(self) -> None:
        """Test parsing JUnit XML with passed testcase."""
        xml_output = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<testsuite>\n"
            '    <testcase name="test_success" file="test.py">\n'
            "    </testcase>\n"
            "</testsuite>"
        )
        result = parse_pytest_junit_xml(xml_output)
        # Passed tests should be ignored
        assert len(result) == 0

    def test_parse_pytest_text_output_file_and_line_format(self) -> None:
        """Test text output with file::test format followed by line format."""
        text_output = (
            "test_example.py::test_function\n"
            "test_example.py:10: FAILED - AssertionError\n"
        )
        result = parse_pytest_text_output(text_output)
        assert len(result) == 1
        assert result[0].file == "test_example.py"

    def test_parse_pytest_output_with_empty_format(self) -> None:
        """Test parse_pytest_output with default empty text."""
        result = parse_pytest_output("", format="text")
        assert result == []

    def test_parse_pytest_output_dispatches_correctly(self) -> None:
        """Test that parse_pytest_output dispatches to correct parser."""
        json_result = parse_pytest_output("{}", format="json")
        assert isinstance(json_result, list)

        text_result = parse_pytest_output("test", format="text")
        assert isinstance(text_result, list)

        xml_result = parse_pytest_output("<xml/>", format="junit")
        assert isinstance(xml_result, list)
