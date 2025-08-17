"""Unit tests for the Actionlint output parser.

These tests validate that the parser handles empty output and typical
``file:line:col: level: message [CODE]`` lines, producing structured issues.
"""

from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output


def test_parse_actionlint_empty():
    assert parse_actionlint_output("") == []


def test_parse_actionlint_lines():
    out = (
        "workflow.yml:10:5: error: unexpected key [AL100]"
        "\nworkflow.yml:12:3: warning: something minor"
    )
    issues = parse_actionlint_output(out)
    assert len(issues) == 2
    i0 = issues[0]
    assert i0.file == "workflow.yml"
    assert i0.line == 10
    assert i0.column == 5
    assert i0.level == "error"
    assert i0.code == "AL100"
    assert "unexpected key" in i0.message
