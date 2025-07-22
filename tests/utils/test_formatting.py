"""Tests for the formatting utilities module.

This module contains tests for the formatting utility functions in Lintro.
"""

import pytest
from unittest.mock import patch
from io import StringIO

from lintro.utils.formatting import (
    get_tool_emoji,
    print_tool_header,
    print_tool_footer,
    read_ascii_art,
    print_summary,
)


@pytest.mark.utils
def test_get_tool_emoji():
    """Test getting emoji for different tools."""
    assert get_tool_emoji("darglint") == "📝"
    assert get_tool_emoji("hadolint") == "🐳"
    assert get_tool_emoji("prettier") == "💅"
    assert get_tool_emoji("ruff") == "🦀"
    assert get_tool_emoji("yamllint") == "📄"
    assert get_tool_emoji("unknown_tool") == "🔧"


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_tool_header(mock_echo):
    """Test printing tool header.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_tool_header("ruff", "check")

    # Verify click.echo was called
    mock_echo.assert_called()
    call_args = mock_echo.call_args[0][0]
    assert "ruff" in call_args
    assert "check" in call_args
    assert "🦀" in call_args


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_tool_header_json_format(mock_echo):
    """Test that tool header is skipped for JSON format.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_tool_header("ruff", "check", output_format="json")
    mock_echo.assert_not_called()


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_tool_footer_success(mock_echo):
    """Test printing tool footer for success case.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_tool_footer(True, 0, tool_name="ruff", action="check")

    mock_echo.assert_called()
    # Check that success message is printed
    calls = mock_echo.call_args_list
    assert any("✓ No issues found" in str(call) for call in calls)


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_tool_footer_failure(mock_echo):
    """Test printing tool footer for failure case.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_tool_footer(False, 5, tool_name="ruff", action="check")

    mock_echo.assert_called()
    # Check that failure message is printed
    calls = mock_echo.call_args_list
    assert any("✗ Found 5 issues" in str(call) for call in calls)


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_tool_footer_json_format(mock_echo):
    """Test that tool footer is skipped for JSON format.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_tool_footer(True, 0, output_format="json", action="check")
    mock_echo.assert_not_called()


@pytest.mark.utils
def test_read_ascii_art():
    """Test reading ASCII art from file.

    This test verifies that the function doesn't crash.
    The actual file reading is tested in integration tests.
    """
    result = read_ascii_art("success.txt")
    assert isinstance(result, list)


@pytest.mark.utils
def test_read_ascii_art_file_not_found():
    """Test reading ASCII art when file doesn't exist."""
    result = read_ascii_art("nonexistent.txt")
    assert result == []


@pytest.mark.utils
def test_print_summary(sample_tool_results):
    """Test printing summary of results.

    Args:
        sample_tool_results: A list of ToolResult objects.
    """
    with patch("lintro.utils.formatting.click.echo") as mock_echo:
        print_summary(sample_tool_results, "check")
        # Verify that summary was printed
        mock_echo.assert_called()
        calls = mock_echo.call_args_list
        summary_text = "".join(str(call) for call in calls)
        assert "EXECUTION SUMMARY" in summary_text
        assert "PASS" in summary_text or "FAIL" in summary_text


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_summary_json_format(mock_echo):
    """Test that summary is skipped for JSON format.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_summary([], "check", output_format="json")
    mock_echo.assert_not_called()


@pytest.mark.utils
@patch("lintro.utils.formatting.click.echo")
def test_print_summary_empty_results(mock_echo):
    """Test printing summary with empty results.

    Args:
        mock_echo: Mock object for click.echo.
    """
    print_summary([], "check")
    # Should not call echo at all for empty results
    mock_echo.assert_not_called()


@pytest.mark.utils
def test_print_summary_stdout(capsys):
    """Test printing summary to stdout using capsys.

    Args:
        capsys: Pytest fixture for capturing stdout/stderr.
    """
    from lintro.models.core.tool_result import ToolResult

    results = [
        ToolResult(name="ruff", success=True, output="", issues_count=0),
        ToolResult(name="yamllint", success=False, output="", issues_count=2),
    ]
    print_summary(results, "check")
    captured = capsys.readouterr()
    content = captured.out
    print("DEBUG: captured output:\n", content)
    assert content.strip() != "", "print_summary did not print any output to stdout."
    assert "Tool" in content and "Status" in content and "Issues" in content
    assert "ruff" in content and "yamllint" in content


@pytest.mark.integration
def test_print_summary_with_real_samples():
    """Integration test: print_summary with real tool results from test_samples."""
    from lintro.models.core.tool_result import ToolResult
    from lintro.formatters.tools.darglint_formatter import format_darglint_issues
    import pathlib

    # Simulate darglint violations
    darglint_file = pathlib.Path("test_samples/darglint_violations.py")
    darglint_issues = [
        type(
            "FakeIssue",
            (),
            dict(
                file=str(darglint_file),
                line=10,
                code="D100",
                message="Missing docstring",
            ),
        )(),
        type(
            "FakeIssue",
            (),
            dict(
                file=str(darglint_file),
                line=30,
                code="D101",
                message="Missing parameter",
            ),
        )(),
    ]
    darglint_formatted = format_darglint_issues(darglint_issues, format="grid")
    darglint_result = ToolResult(
        name="darglint",
        success=False,
        output="",
        issues_count=len(darglint_issues),
        formatted_output=darglint_formatted,
    )
    # Simulate yamllint violations
    yamllint_file = pathlib.Path("test_samples/yaml_violations.yml")
    yamllint_issues = [
        type(
            "FakeIssue",
            (),
            dict(
                file=str(yamllint_file),
                line=7,
                code="YAML001",
                message="Trailing spaces",
            ),
        )(),
    ]
    from lintro.formatters.tools.ruff_formatter import FORMAT_MAP as RUFF_FORMAT_MAP

    yamllint_formatted = RUFF_FORMAT_MAP["grid"].format(
        ["File", "Line", "Code", "Message"],
        [[str(yamllint_file), "7", "YAML001", "Trailing spaces"]],
    )
    yamllint_result = ToolResult(
        name="yamllint",
        success=False,
        output="",
        issues_count=len(yamllint_issues),
        formatted_output=yamllint_formatted,
    )
    output = StringIO()
    print_summary([darglint_result, yamllint_result], "check", file=output)
    content = output.getvalue()
    # Debug print if assertion fails
    if not ("darglint" in content and "yamllint" in content and "FAIL" in content):
        print("Captured output:\n", content)
    assert "darglint" in content
    assert "yamllint" in content
    assert "FAIL" in content
    assert "Tool" in content and "Status" in content and "Issues" in content


@pytest.mark.utils
def test_print_tool_header_with_file():
    """Test printing tool header to a file."""
    output = StringIO()
    print_tool_header("ruff", "check", file=output)
    content = output.getvalue()
    assert "ruff" in content
    assert "check" in content
    assert "🦀" in content


@pytest.mark.utils
def test_print_tool_footer_with_file():
    """Test printing tool footer to a file."""
    output = StringIO()
    print_tool_footer(True, 0, file=output, action="check")
    content = output.getvalue()
    assert "No issues found" in content
