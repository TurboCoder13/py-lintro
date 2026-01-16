"""Unit tests for Gitleaks output parsing."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.parsers.gitleaks.gitleaks_issue import GitleaksIssue
from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output
from lintro.plugins import ToolRegistry


def test_parse_gitleaks_valid_output() -> None:
    """Parse a representative Gitleaks JSON result and validate fields."""
    sample_output = json.dumps([
        {
            "Description": "AWS Access Key",
            "StartLine": 10,
            "EndLine": 10,
            "StartColumn": 15,
            "EndColumn": 35,
            "Match": "AKIAIOSFODNN7EXAMPLE",
            "Secret": "AKIAIOSFODNN7EXAMPLE",
            "File": "config.py",
            "SymlinkFile": "",
            "Commit": "",
            "Entropy": 3.5,
            "Author": "",
            "Email": "",
            "Date": "",
            "Message": "",
            "Tags": ["key", "AWS"],
            "RuleID": "aws-access-key-id",
            "Fingerprint": "config.py:aws-access-key-id:10",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    issue = issues[0]
    assert_that(issue.file).is_equal_to("config.py")
    assert_that(issue.line).is_equal_to(10)
    assert_that(issue.column).is_equal_to(15)
    assert_that(issue.end_line).is_equal_to(10)
    assert_that(issue.end_column).is_equal_to(35)
    assert_that(issue.rule_id).is_equal_to("aws-access-key-id")
    assert_that(issue.description).is_equal_to("AWS Access Key")
    assert_that(issue.secret).is_equal_to("AKIAIOSFODNN7EXAMPLE")
    assert_that(issue.entropy).is_equal_to(3.5)
    assert_that(issue.tags).is_equal_to(["key", "AWS"])
    assert_that(issue.fingerprint).is_equal_to("config.py:aws-access-key-id:10")


def test_parse_gitleaks_multiple_findings() -> None:
    """Parser should handle multiple findings."""
    sample_output = json.dumps([
        {
            "Description": "AWS Access Key",
            "StartLine": 5,
            "EndLine": 5,
            "StartColumn": 1,
            "EndColumn": 20,
            "File": "a.py",
            "RuleID": "aws-access-key-id",
            "Fingerprint": "a.py:aws-access-key-id:5",
        },
        {
            "Description": "GitHub Token",
            "StartLine": 10,
            "EndLine": 10,
            "StartColumn": 1,
            "EndColumn": 40,
            "File": "b.py",
            "RuleID": "github-pat",
            "Fingerprint": "b.py:github-pat:10",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(2)
    assert_that(issues[0].file).is_equal_to("a.py")
    assert_that(issues[0].rule_id).is_equal_to("aws-access-key-id")
    assert_that(issues[1].file).is_equal_to("b.py")
    assert_that(issues[1].rule_id).is_equal_to("github-pat")


def test_parse_gitleaks_empty_array() -> None:
    """Empty array should return no issues."""
    issues = parse_gitleaks_output(output="[]")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_empty_string() -> None:
    """Empty string should return no issues."""
    issues = parse_gitleaks_output(output="")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_none_input() -> None:
    """None input should return no issues."""
    issues = parse_gitleaks_output(output=None)
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_whitespace_only() -> None:
    """Whitespace-only input should return no issues."""
    issues = parse_gitleaks_output(output="   \n\t  ")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_invalid_json() -> None:
    """Invalid JSON should return empty list and log warning."""
    issues = parse_gitleaks_output(output="not valid json")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_non_array_json() -> None:
    """Non-array JSON should return empty list."""
    issues = parse_gitleaks_output(output='{"not": "an array"}')
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_handles_malformed_finding_gracefully() -> None:
    """Malformed findings should be skipped."""
    sample_output = json.dumps([
        None,
        42,
        {"File": "", "StartLine": 10},  # Empty file
        {"StartLine": 10},  # Missing File
        {
            "File": "valid.py",
            "StartLine": 5,
            "RuleID": "test-rule",
            "Description": "Valid finding",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    # Only the last valid finding should be parsed
    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].file).is_equal_to("valid.py")


def test_parse_gitleaks_git_history_fields() -> None:
    """Parser should handle git history fields from commit scanning."""
    sample_output = json.dumps([
        {
            "Description": "API Key",
            "StartLine": 1,
            "EndLine": 1,
            "StartColumn": 1,
            "EndColumn": 30,
            "File": "secret.py",
            "Commit": "abc123def456",
            "Author": "John Doe",
            "Email": "john@example.com",
            "Date": "2024-01-15T10:30:00Z",
            "Message": "Add configuration",
            "RuleID": "generic-api-key",
            "Fingerprint": "secret.py:generic-api-key:1:abc123def456",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    issue = issues[0]
    assert_that(issue.commit).is_equal_to("abc123def456")
    assert_that(issue.author).is_equal_to("John Doe")
    assert_that(issue.email).is_equal_to("john@example.com")
    assert_that(issue.date).is_equal_to("2024-01-15T10:30:00Z")
    assert_that(issue.commit_message).is_equal_to("Add configuration")


def test_gitleaks_issue_display_row() -> None:
    """GitleaksIssue should produce correct display row."""
    issue = GitleaksIssue(
        file="config.py",
        line=10,
        column=5,
        rule_id="aws-access-key-id",
        description="AWS Access Key",
        secret="AKIAEXAMPLE",
    )

    row = issue.to_display_row()

    assert_that(row["file"]).is_equal_to("config.py")
    assert_that(row["line"]).is_equal_to("10")
    assert_that(row["column"]).is_equal_to("5")
    assert_that(row["code"]).is_equal_to("aws-access-key-id")
    assert_that(row["message"]).contains("AWS Access Key")
    assert_that(row["message"]).contains("[REDACTED]")


def test_gitleaks_issue_message_without_secret() -> None:
    """GitleaksIssue message should not show REDACTED when no secret."""
    issue = GitleaksIssue(
        file="test.py",
        line=1,
        column=1,
        rule_id="test-rule",
        description="Test Description",
        secret="",
    )

    assert_that(issue.message).is_equal_to("[test-rule] Test Description")
    assert_that(issue.message).does_not_contain("REDACTED")


def test_gitleaks_check_parses_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """GitleaksPlugin.check should parse JSON output correctly.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path fixture.
    """
    p = tmp_path / "secret.py"
    p.write_text("API_KEY = 'sk_test_example'\n")

    sample = [
        {
            "Description": "Generic API Key",
            "StartLine": 1,
            "EndLine": 1,
            "StartColumn": 11,
            "EndColumn": 27,
            "File": str(p),
            "RuleID": "generic-api-key",
            "Fingerprint": f"{p}:generic-api-key:1",
        },
    ]

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        timeout: int,
        **kwargs: Any,
    ) -> SimpleNamespace:
        # Handle version check calls (check for --version flag)
        if "--version" in cmd or "version" in cmd:
            return SimpleNamespace(stdout="8.18.0", stderr="", returncode=0)
        # Handle actual check calls
        return SimpleNamespace(
            stdout=json.dumps(sample),
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr("subprocess.run", fake_run)
    tool = ToolRegistry.get("gitleaks")
    assert_that(tool).is_not_none()

    result: ToolResult = tool.check([str(tmp_path)], {})

    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("gitleaks")
    assert_that(result.success).is_true()  # success=True means tool ran, not no issues
    assert_that(result.issues_count).is_equal_to(1)


def test_gitleaks_check_handles_no_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """GitleaksPlugin.check should handle clean output.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path fixture.
    """
    p = tmp_path / "clean.py"
    p.write_text("x = 1\n")

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        timeout: int,
        **kwargs: Any,
    ) -> SimpleNamespace:
        # Handle version check calls (check for --version flag)
        if "--version" in cmd or "version" in cmd:
            return SimpleNamespace(stdout="8.18.0", stderr="", returncode=0)
        # Handle actual check calls - empty array means no secrets
        return SimpleNamespace(stdout="[]", stderr="", returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)
    tool = ToolRegistry.get("gitleaks")
    assert_that(tool).is_not_none()

    result: ToolResult = tool.check([str(tmp_path)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_gitleaks_check_handles_unparseable_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """On unparseable output, GitleaksPlugin.check should return empty issues.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path fixture.
    """
    p = tmp_path / "test.py"
    p.write_text("x = 1\n")

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        timeout: int,
        **kwargs: Any,
    ) -> SimpleNamespace:
        # Handle version check calls (check for --version flag)
        if "--version" in cmd or "version" in cmd:
            return SimpleNamespace(stdout="8.18.0", stderr="", returncode=0)
        # Handle actual check calls - invalid JSON
        return SimpleNamespace(stdout="not json", stderr="error", returncode=1)

    monkeypatch.setattr("subprocess.run", fake_run)
    tool = ToolRegistry.get("gitleaks")
    assert_that(tool).is_not_none()

    result: ToolResult = tool.check([str(tmp_path)], {})

    assert_that(isinstance(result, ToolResult)).is_true()
    assert_that(result.name).is_equal_to("gitleaks")
    # Parser returns empty list for invalid JSON, success depends on returncode
    assert_that(result.issues_count).is_equal_to(0)


def test_gitleaks_entropy_parsing() -> None:
    """Parser should correctly handle entropy as float."""
    sample_output = json.dumps([
        {
            "File": "test.py",
            "StartLine": 1,
            "Entropy": 4.25,
            "RuleID": "test",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].entropy).is_equal_to(4.25)


def test_gitleaks_entropy_as_int() -> None:
    """Parser should handle entropy as integer."""
    sample_output = json.dumps([
        {
            "File": "test.py",
            "StartLine": 1,
            "Entropy": 4,
            "RuleID": "test",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].entropy).is_equal_to(4.0)


def test_gitleaks_tags_empty_list() -> None:
    """Parser should handle empty tags list."""
    sample_output = json.dumps([
        {
            "File": "test.py",
            "StartLine": 1,
            "Tags": [],
            "RuleID": "test",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].tags).is_equal_to([])


def test_gitleaks_tags_none() -> None:
    """Parser should handle missing tags field."""
    sample_output = json.dumps([
        {
            "File": "test.py",
            "StartLine": 1,
            "RuleID": "test",
        },
    ])

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].tags).is_equal_to([])
