"""Unit tests for Bandit output parsing and tool JSON extraction."""

import json
from types import SimpleNamespace

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.parsers.bandit.bandit_parser import parse_bandit_output
from lintro.tools.implementations.tool_bandit import BanditTool


def test_parse_bandit_valid_output() -> None:
    """Parse a representative Bandit JSON result and validate fields."""
    sample_output = {
        "results": [
            {
                "filename": "test.py",
                "line_number": 10,
                "col_offset": 4,
                "test_id": "B602",
                "test_name": ("subprocess_popen_with_shell_equals_true"),
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": (
                    "subprocess call with shell=True identified, security issue."
                ),
                "more_info": (
                    "https://bandit.readthedocs.io/en/1.8.6/plugins/"
                    "b602_subprocess_popen_with_shell_equals_true.html"
                ),
                "issue_cwe": {
                    "id": 78,
                    "link": "https://cwe.mitre.org/data/definitions/78.html",
                },
                "code": "subprocess.call(user_input, shell=True)",
                "line_range": [10],
            }
        ]
    }
    issues = parse_bandit_output(sample_output)
    assert_that(len(issues)).is_equal_to(1)
    issue = issues[0]
    assert_that(issue.file).is_equal_to("test.py")
    assert_that(issue.line).is_equal_to(10)
    assert_that(issue.col_offset).is_equal_to(4)
    assert_that(issue.test_id).is_equal_to("B602")
    assert_that(issue.issue_severity).is_equal_to("HIGH")
    assert_that(issue.issue_confidence).is_equal_to("HIGH")
    assert_that(issue.issue_text).contains("shell=True")


def test_parse_bandit_empty_results() -> None:
    """Ensure an empty results list returns no issues."""
    issues = parse_bandit_output({"results": []})
    assert_that(issues).is_equal_to([])


def test_parse_bandit_missing_results_key() -> None:
    """Missing results should behave as empty list (no crash)."""
    issues = parse_bandit_output({})
    assert_that(issues).is_equal_to([])


def test_parse_bandit_handles_malformed_issue_gracefully(caplog) -> None:
    """Malformed issue entries should be skipped with a warning.

    Args:
        caplog: Pytest logging capture fixture.
    """
    malformed = {"results": [None, 42, {"filename": "x.py", "line_number": "NaN"}]}
    issues = parse_bandit_output(malformed)
    assert_that(issues).is_equal_to([])


def test_bandit_check_parses_mixed_output_json(monkeypatch, tmp_path):
    """BanditTool.check should parse JSON amidst mixed stdout/stderr text.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path fixture.
    """
    p = tmp_path / "a.py"
    p.write_text("print('hello')\n")
    sample = {
        "errors": [],
        "results": [
            {
                "filename": str(p),
                "line_number": 1,
                "col_offset": 0,
                "issue_severity": "LOW",
                "issue_confidence": "HIGH",
                "test_id": "B101",
                "test_name": "assert_used",
                "issue_text": "Use of assert detected.",
                "more_info": "https://example.com",
                "line_range": [1],
            }
        ],
    }
    mixed_stdout = "Working... 100%\n" + json.dumps(sample) + "\n"
    mixed_stderr = "[main] INFO done\n"

    def fake_run(cmd, capture_output, text, timeout, cwd):
        return SimpleNamespace(stdout=mixed_stdout, stderr=mixed_stderr, returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)
    tool = BanditTool()
    result: ToolResult = tool.check([str(p)])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("bandit")
    assert_that(result.success is True).is_true()
    assert_that(result.issues_count).is_equal_to(1)


def test_bandit_check_handles_unparseable_output(monkeypatch, tmp_path):
    """On unparseable output, BanditTool.check should fail gracefully.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path fixture.
    """
    p = tmp_path / "b.py"
    p.write_text("x=1\n")

    def fake_run(cmd, capture_output, text, timeout, cwd):
        return SimpleNamespace(stdout="nonsense", stderr="also nonsense", returncode=1)

    monkeypatch.setattr("subprocess.run", fake_run)
    tool = BanditTool()
    result: ToolResult = tool.check([str(p)])
    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("bandit")
    assert_that(result.success is False).is_true()
    assert_that(result.issues_count).is_equal_to(0)
