"""Unit tests for Biome parser functionality."""

from lintro.parsers.biome.biome_parser import _char_to_line_column, parse_biome_output


def test_char_to_line_column_basic() -> None:
    """Test basic character to line/column conversion."""
    source = "line1\nline2\nline3"
    assert _char_to_line_column(source, 0) == (1, 1)  # Start of file
    assert _char_to_line_column(source, 5) == (1, 6)  # '1' in "line1"
    assert _char_to_line_column(source, 6) == (2, 1)  # Start of line2
    assert _char_to_line_column(source, 11) == (2, 6)  # '2' in "line2"
    assert _char_to_line_column(source, 12) == (3, 1)  # Start of line3


def test_char_to_line_column_edge_cases() -> None:
    """Test edge cases for character to line/column conversion."""
    # Empty source
    assert _char_to_line_column("", 0) == (1, 1)
    assert _char_to_line_column("", 10) == (1, 1)  # Beyond length

    # Negative position
    assert _char_to_line_column("test", -1) == (1, 1)

    # Position beyond source length
    assert _char_to_line_column("test", 100) == (1, 5)  # Clamped to end

    # Source with only newlines
    assert _char_to_line_column("\n\n\n", 0) == (1, 1)
    assert _char_to_line_column("\n\n\n", 1) == (2, 1)
    assert _char_to_line_column("\n\n\n", 2) == (3, 1)
    assert _char_to_line_column("\n\n\n", 3) == (4, 1)


def test_parse_biome_output_empty() -> None:
    """Test parsing empty Biome output."""
    issues = parse_biome_output("")
    assert issues == []

    issues = parse_biome_output("some non-json text")
    assert issues == []


def test_parse_biome_output_malformed_json() -> None:
    """Test parsing malformed JSON Biome output."""
    issues = parse_biome_output("{invalid json")
    assert issues == []


def test_parse_biome_output_with_extra_text() -> None:
    """Test parsing Biome output with extra text after JSON."""
    json_content = '{"summary":{"changed":0,"unchanged":1,"matches":0,"duration":{"secs":0,"nanos":100},"scannerDuration":{"secs":0,"nanos":50},"errors":1,"warnings":0,"infos":0,"skipped":0,"suggestedFixesSkipped":0,"diagnosticsNotPrinted":0},"diagnostics":[{"category":"lint/test","severity":"error","description":"Test error","message":[{"elements":[],"content":"Test error"}],"location":{"path":{"file":"test.js"},"span":[10,15],"sourceCode":"test code"},"tags":[]}]}'
    extra_text = "\nThe --json option is unstable/experimental...\n"

    issues = parse_biome_output(json_content + extra_text)
    assert len(issues) == 1
    assert issues[0].file == "test.js"
    assert issues[0].code == "lint/test"
    assert issues[0].severity == "error"


def test_parse_biome_output_single_issue() -> None:
    """Test parsing Biome output with a single diagnostic."""
    json_output = """{
        "summary": {"changed": 0, "unchanged": 1, "errors": 1, "warnings": 0, "infos": 0},
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
    assert len(issues) == 1

    issue = issues[0]
    assert issue.file == "test.js"
    assert issue.code == "lint/suspicious/noDoubleEquals"
    assert issue.message == "Using == may be unsafe"
    assert issue.severity == "error"
    assert issue.fixable is True

    # Test line/column calculation
    # Biome uses absolute file positions, sourceCode is just context
    # The exact line/column depends on the sourceCode snippet provided
    assert issue.line == 1  # All positions resolve to line 1 in the snippet
    assert issue.column >= 1  # Column is calculated from the sourceCode snippet
    assert issue.end_line is None  # End position beyond snippet length
    assert issue.end_column is None


def test_parse_biome_output_multiple_issues() -> None:
    """Test parsing Biome output with multiple diagnostics."""
    json_output = """{
        "summary": {"changed": 0, "unchanged": 1, "errors": 2, "warnings": 1, "infos": 0},
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
    assert len(issues) == 2

    # First issue (error)
    assert issues[0].severity == "error"
    assert issues[0].fixable is True

    # Second issue (warning)
    assert issues[1].severity == "warning"
    assert issues[1].fixable is False


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
    assert len(issues) == 1

    issue = issues[0]
    assert issue.file == "test.js"
    assert issue.line == 1
    assert issue.column == 1
    assert issue.end_line is None  # No sourceCode provided, so no end position
    assert issue.end_column is None
    assert issue.fixable is False
    assert issue.message == "Test"
    assert issue.severity == "info"


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
    assert len(issues) == 0  # Should skip issues without file path


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
    assert len(issues) == 1
    assert issues[0].message == "Complex message"
