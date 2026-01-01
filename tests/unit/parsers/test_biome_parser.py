"""Unit tests for Biome parser functionality."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.biome.biome_parser import _char_to_line_column, parse_biome_output


def test_char_to_line_column_basic() -> None:
    """Test basic character to line/column conversion."""
    source = "line1\nline2\nline3"
    assert_that(_char_to_line_column(source, 0)).is_equal_to((1, 1))  # Start of file
    assert_that(_char_to_line_column(source, 5)).is_equal_to(
        (1, 6),
    )  # '\n' after "line1"
    assert_that(_char_to_line_column(source, 6)).is_equal_to((2, 1))  # Start of "line2"
    assert_that(_char_to_line_column(source, 11)).is_equal_to(
        (2, 6),
    )  # '\n' after "line2"
    assert_that(_char_to_line_column(source, 12)).is_equal_to((3, 1))  # Start of line3


def test_char_to_line_column_edge_cases() -> None:
    """Test edge cases for character to line/column conversion."""
    # Empty source
    assert_that(_char_to_line_column("", 0)).is_equal_to((1, 1))
    assert_that(_char_to_line_column("", 10)).is_equal_to((1, 1))  # Beyond length

    # Negative position
    assert_that(_char_to_line_column("test", -1)).is_equal_to((1, 1))

    # Position beyond source length
    assert_that(_char_to_line_column("test", 100)).is_equal_to((1, 5))  # Clamped to end

    # Source with only newlines
    assert_that(_char_to_line_column("\n\n\n", 0)).is_equal_to((1, 1))
    assert_that(_char_to_line_column("\n\n\n", 1)).is_equal_to((2, 1))
    assert_that(_char_to_line_column("\n\n\n", 2)).is_equal_to((3, 1))
    assert_that(_char_to_line_column("\n\n\n", 3)).is_equal_to((4, 1))


def test_parse_biome_output_empty() -> None:
    """Test parsing empty Biome output."""
    issues = parse_biome_output("")
    assert_that(issues).is_empty()

    issues = parse_biome_output("some non-json text")
    assert_that(issues).is_empty()


def test_parse_biome_output_malformed_json() -> None:
    """Test parsing malformed JSON Biome output."""
    issues = parse_biome_output("{invalid json")
    assert_that(issues).is_empty()


def test_parse_biome_output_with_extra_text() -> None:
    """Test parsing Biome output with extra text after JSON."""
    json_content = (
        '{"summary":{"changed":0,"unchanged":1,"matches":0,"duration":{"secs":0,"nanos":100},'
        '"scannerDuration":{"secs":0,"nanos":50},"errors":1,"warnings":0,"infos":0,"skipped":0,'
        '"suggestedFixesSkipped":0,"diagnosticsNotPrinted":0},"diagnostics":'
        '[{"category":"lint/test","severity":"error","description":"Test error",'
        '"message":[{"elements":[],"content":"Test error"}],"location":'
        '{"path":{"file":"test.js"},"span":[10,15],"sourceCode":"test code"},'
        '"tags":[]}]}'
    )
    extra_text = "\nThe --json option is unstable/experimental...\n"

    issues = parse_biome_output(json_content + extra_text)
    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.js")
    assert_that(issues[0].code).is_equal_to("lint/test")
    assert_that(issues[0].severity).is_equal_to("error")


def test_parse_biome_output_single_issue() -> None:
    """Test parsing Biome output with a single diagnostic."""
    json_output = """{
        "summary": {"changed": 0, "unchanged": 1, "errors": 1,
                    "warnings": 0, "infos": 0},
        "diagnostics": [{
            "category": "lint/suspicious/noDoubleEquals",
            "severity": "error",
            "description": "Using == may be unsafe",
            "message": [{"elements": [], "content": "Using == may be unsafe"}],
            "location": {
                "path": {"file": "test.js"},
                "span": [20, 22],
                "sourceCode": "if (a == b) {"
            },
            "tags": ["fixable"]
        }]
    }"""

    issues = parse_biome_output(json_output)
    assert_that(issues).is_length(1)

    issue = issues[0]
    assert_that(issue.file).is_equal_to("test.js")
    assert_that(issue.code).is_equal_to("lint/suspicious/noDoubleEquals")
    assert_that(issue.message).is_equal_to("Using == may be unsafe")
    assert_that(issue.severity).is_equal_to("error")
    assert_that(issue.fixable).is_true()

    # Test line/column calculation
    # Biome uses absolute file positions, sourceCode is just context
    # The exact line/column depends on the sourceCode snippet provided
    # All positions resolve to line 1 in the snippet
    assert_that(issue.line).is_equal_to(1)
    # Column is calculated from the sourceCode snippet
    assert_that(issue.column).is_greater_than_or_equal_to(1)
    assert_that(issue.end_line).is_none()  # End position beyond snippet length
    assert_that(issue.end_column).is_none()


def test_parse_biome_output_multiple_issues() -> None:
    """Test parsing Biome output with multiple diagnostics."""
    json_output = """{
        "summary": {"changed": 0, "unchanged": 1, "errors": 2,
                    "warnings": 1, "infos": 0},
        "diagnostics": [
            {
                "category": "lint/suspicious/noDoubleEquals",
                "severity": "error",
                "description": "Using == may be unsafe",
                "location": {"path": {"file": "test.js"}, "span": [20, 22]},
                "tags": ["fixable"]
            },
            {
                "category": "lint/correctness/noUnusedVariables",
                "severity": "warning",
                "description": "Unused variable",
                "location": {"path": {"file": "test.js"}, "span": [5, 10]},
                "tags": []
            }
        ]
    }"""

    issues = parse_biome_output(json_output)
    assert_that(issues).is_length(2)

    # First issue (error)
    assert_that(issues[0].severity).is_equal_to("error")
    assert_that(issues[0].fixable).is_true()

    # Second issue (warning)
    assert_that(issues[1].severity).is_equal_to("warning")
    assert_that(issues[1].fixable).is_false()


def test_parse_biome_output_missing_fields() -> None:
    """Test parsing Biome output with missing optional fields."""
    json_output = """{
        "diagnostics": [{
            "category": "lint/test",
            "severity": "info",
            "description": "Test",
            "location": {"path": {"file": "test.js"}, "span": [0, 1]},
            "tags": []
        }]
    }"""

    issues = parse_biome_output(json_output)
    assert_that(issues).is_length(1)

    issue = issues[0]
    assert_that(issue.file).is_equal_to("test.js")
    assert_that(issue.line).is_equal_to(1)
    assert_that(issue.column).is_equal_to(1)
    assert_that(issue.end_line).is_none()  # No sourceCode provided, so no end position
    assert_that(issue.end_column).is_none()
    assert_that(issue.fixable).is_false()
    assert_that(issue.message).is_equal_to("Test")
    assert_that(issue.severity).is_equal_to("info")


def test_parse_biome_output_malformed_location() -> None:
    """Test parsing Biome output with malformed location data."""
    json_output = """{
        "diagnostics": [{
            "category": "lint/test",
            "severity": "error",
            "description": "Test",
            "location": {},
            "tags": []
        }]
    }"""

    issues = parse_biome_output(json_output)
    assert_that(issues).is_length(0)  # Should skip issues without file path


def test_parse_biome_output_complex_message() -> None:
    """Test parsing Biome output with complex message structure."""
    json_output = """{
        "diagnostics": [{
            "category": "lint/test",
            "severity": "error",
            "description": "Complex message",
            "message": [
                {"elements": [], "content": "This is "},
                {"elements": ["Emphasis"], "content": "emphasized"},
                {"elements": [], "content": " text."}
            ],
            "location": {"path": {"file": "test.js"}, "span": [0, 1]},
            "tags": []
        }]
    }"""

    issues = parse_biome_output(json_output)
    assert_that(issues).is_length(1)
    assert_that(issues[0].message).is_equal_to("Complex message")
