"""Unit tests for pytest parser."""

from assertpy import assert_that

from lintro.parsers.pytest.pytest_parser import (
    parse_pytest_json_output,
    parse_pytest_junit_xml,
    parse_pytest_output,
    parse_pytest_text_output,
)


def test_parse_pytest_json_output_empty() -> None:
    """Test parsing empty JSON output."""
    result = parse_pytest_json_output("")
    assert_that(result).is_empty()

    result = parse_pytest_json_output("{}")
    assert_that(result).is_empty()

    result = parse_pytest_json_output("[]")
    assert_that(result).is_empty()


def test_parse_pytest_json_output_valid() -> None:
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
    assert_that(result).is_length(2)

    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].line).is_equal_to(10)
    assert_that(result[0].test_name).is_equal_to("test_failure")
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).is_equal_to("AssertionError: Expected 1 but got 2")
    assert_that(result[0].duration).is_equal_to(0.001)
    assert_that(result[0].node_id).is_equal_to("test_example.py::test_failure")

    assert_that(result[1].file).is_equal_to("test_example.py")
    assert_that(result[1].line).is_equal_to(15)
    assert_that(result[1].test_name).is_equal_to("test_error")
    assert_that(result[1].test_status).is_equal_to("ERROR")
    assert_that(result[1].message).is_equal_to("ZeroDivisionError: division by zero")
    assert_that(result[1].duration).is_equal_to(0.002)
    assert_that(result[1].node_id).is_equal_to("test_example.py::test_error")


def test_parse_pytest_text_output_empty() -> None:
    """Test parsing empty text output."""
    result = parse_pytest_text_output("")
    assert_that(result).is_empty()


def test_parse_pytest_text_output_failures() -> None:
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
    assert_that(result).is_length(3)

    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].test_name).is_equal_to("test_failure")
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).is_equal_to("AssertionError: Expected 1 but got 2")

    assert_that(result[1].file).is_equal_to("test_example.py")
    assert_that(result[1].test_name).is_equal_to("test_error")
    assert_that(result[1].test_status).is_equal_to("ERROR")
    assert_that(result[1].message).is_equal_to("ZeroDivisionError: division by zero")

    assert_that(result[2].file).is_equal_to("test_example.py")
    assert_that(result[2].test_name).is_equal_to("test_another_failure")
    assert_that(result[2].test_status).is_equal_to("FAILED")
    assert_that(result[2].message).is_equal_to("ValueError: invalid value")


def test_parse_pytest_text_output_line_format() -> None:
    """Test parsing text output with line number format."""
    text_output = (
        "test_example.py:10: FAILED - AssertionError: Expected 1 but got 2\n"
        "test_example.py:15: ERROR - ZeroDivisionError: division by zero\n"
    )

    result = parse_pytest_text_output(text_output)
    assert_that(result).is_length(2)

    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].line).is_equal_to(10)
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).is_equal_to("AssertionError: Expected 1 but got 2")

    assert_that(result[1].file).is_equal_to("test_example.py")
    assert_that(result[1].line).is_equal_to(15)
    assert_that(result[1].test_status).is_equal_to("ERROR")
    assert_that(result[1].message).is_equal_to("ZeroDivisionError: division by zero")


def test_parse_pytest_junit_xml_empty() -> None:
    """Test parsing empty JUnit XML output."""
    result = parse_pytest_junit_xml("")
    assert_that(result).is_empty()


def test_parse_pytest_junit_xml_valid() -> None:
    """Test parsing valid JUnit XML output."""
    xml_output = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuite name="pytest" tests="2" failures="1" errors="1" time="0.003">\n'
        '    <testcase name="test_failure" file="test_example.py" line="10" '
        'time="0.001" classname="TestExample">\n'
        '        <failure message="AssertionError: Expected 1 but got 2">'
        "Traceback (most recent call last):\n"
        '  File "test_example.py", line 10, in test_failure\n'
        "    assert_that(1).is_equal_to(2)\n"
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
    assert_that(result).is_length(2)

    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].line).is_equal_to(10)
    assert_that(result[0].test_name).is_equal_to("test_failure")
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).contains("AssertionError: Expected 1 but got 2")
    assert_that(result[0].duration).is_equal_to(0.001)
    assert_that(result[0].node_id).is_equal_to("TestExample::test_failure")

    assert_that(result[1].file).is_equal_to("test_example.py")
    assert_that(result[1].line).is_equal_to(15)
    assert_that(result[1].test_name).is_equal_to("test_error")
    assert_that(result[1].test_status).is_equal_to("ERROR")
    assert_that(result[1].message).contains("ZeroDivisionError: division by zero")
    assert_that(result[1].duration).is_equal_to(0.002)
    assert_that(result[1].node_id).is_equal_to("TestExample::test_error")


def test_parse_pytest_output_format_dispatch() -> None:
    """Test that parse_pytest_output dispatches to correct parser."""
    # Test JSON format
    json_output = '{"tests": []}'
    result = parse_pytest_output(json_output, format="json")
    assert_that(result).is_instance_of(list)

    # Test text format
    text_output = "FAILED test.py::test - AssertionError"
    result = parse_pytest_output(text_output, format="text")
    assert_that(result).is_instance_of(list)

    # Test junit format
    xml_output = '<?xml version="1.0"?><testsuite></testsuite>'
    result = parse_pytest_output(xml_output, format="junit")
    assert_that(result).is_instance_of(list)

    # Test default format (text)
    result = parse_pytest_output(text_output)
    assert_that(result).is_instance_of(list)


def test_parse_pytest_json_output_malformed() -> None:
    """Test parsing malformed JSON output."""
    malformed_json = '{"tests": [{"incomplete": "object"'
    result = parse_pytest_json_output(malformed_json)
    assert_that(result).is_empty()


def test_parse_pytest_junit_xml_malformed() -> None:
    """Test parsing malformed JUnit XML output."""
    malformed_xml = "<testsuite><testcase><incomplete>"
    result = parse_pytest_junit_xml(malformed_xml)
    assert_that(result).is_empty()


def test_parse_pytest_text_output_ansi_codes() -> None:
    """Test parsing text output with ANSI color codes."""
    text_with_ansi = (
        "\x1b[31mFAILED\x1b[0m test_example.py::test_failure - AssertionError"
    )
    result = parse_pytest_text_output(text_with_ansi)
    assert_that(result).is_length(1)
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).is_equal_to("AssertionError")


def test_parse_pytest_json_output_missing_optional_fields() -> None:
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
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].line).is_equal_to(0)
    assert_that(result[0].duration).is_equal_to(0.0)


def test_parse_pytest_json_output_alternative_list_format() -> None:
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
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test_example.py")


def test_parse_pytest_json_output_with_call_message() -> None:
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
    assert_that(result).is_length(1)
    # Should prefer call.longrepr
    assert_that(result[0].message).is_equal_to("Error in call")


def test_parse_pytest_json_output_passed_test_ignored() -> None:
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
    assert_that(result).is_length(1)
    assert_that(result[0].test_name).is_equal_to("test_failure")


def test_parse_pytest_text_output_alternative_failure_format() -> None:
    """Test parsing text output with alternative failure format."""
    text_output = "FAILED test_example.py::test_failure Some error message"
    result = parse_pytest_text_output(text_output)
    # Should parse using alternative pattern
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test_example.py")
    assert_that(result[0].test_name).is_equal_to("test_failure")
    assert_that(result[0].test_status).is_equal_to("FAILED")
    assert_that(result[0].message).contains("Some error message")


def test_parse_pytest_text_output_multiple_failures() -> None:
    """Test parsing text output with multiple failure types."""
    text_output = (
        "FAILED test_a.py::test_1 - Error 1\n"
        "ERROR test_b.py::test_2 - Error 2\n"
        "FAILED test_c.py::test_3 - Error 3\n"
    )
    result = parse_pytest_text_output(text_output)
    assert_that(result).is_length(3)


def test_parse_pytest_junit_xml_missing_attributes() -> None:
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
    assert_that(result).is_length(1)
    assert_that(result[0].test_name).is_equal_to("test_failure")


def test_parse_pytest_junit_xml_without_message_attribute() -> None:
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
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("Error text content")


def test_parse_pytest_junit_xml_no_failure_or_error() -> None:
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
    assert_that(result).is_length(0)


def test_parse_pytest_text_output_file_and_line_format() -> None:
    """Test text output with file::test format followed by line format."""
    text_output = (
        "test_example.py::test_function\ntest_example.py:10: FAILED - AssertionError\n"
    )
    result = parse_pytest_text_output(text_output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("test_example.py")


def test_parse_pytest_output_with_empty_format() -> None:
    """Test parse_pytest_output with default empty text."""
    result = parse_pytest_output("", format="text")
    assert_that(result).is_empty()


def test_parse_pytest_output_dispatches_correctly() -> None:
    """Test that parse_pytest_output dispatches to correct parser."""
    json_result = parse_pytest_output("{}", format="json")
    assert_that(json_result).is_instance_of(list)

    text_result = parse_pytest_output("test", format="text")
    assert_that(text_result).is_instance_of(list)

    xml_result = parse_pytest_output("<xml/>", format="junit")
    assert_that(xml_result).is_instance_of(list)
