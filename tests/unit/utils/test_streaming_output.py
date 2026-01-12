"""Tests for lintro.utils.streaming_output module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from lintro.enums.action import Action
from lintro.models.core.tool_result import ToolResult
from lintro.utils.streaming_output import (
    StreamingResultHandler,
    create_streaming_handler,
)


@pytest.fixture
def mock_tool_result() -> ToolResult:
    """Create a mock ToolResult for testing.

    Returns:
        A ToolResult with success=True and 2 issues.
    """
    return ToolResult(
        name="test_tool",
        success=True,
        issues_count=2,
        output="Test output",
    )


@pytest.fixture
def mock_tool_result_with_issues() -> ToolResult:
    """Create a mock ToolResult with issues.

    Returns:
        A ToolResult with success=False and 1 issue.
    """
    mock_issue = MagicMock()
    mock_issue.file = "test.py"
    mock_issue.line = 10
    mock_issue.column = 5
    mock_issue.message = "Test error"

    return ToolResult(
        name="test_tool",
        success=False,
        issues_count=1,
        output="Error output",
        issues=[mock_issue],
    )


@pytest.fixture
def mock_fix_result() -> ToolResult:
    """Create a mock ToolResult for fix action.

    Returns:
        A ToolResult with fix counts set.
    """
    result = ToolResult(
        name="test_tool",
        success=True,
        issues_count=0,
        output="Fixed",
    )
    result.fixed_issues_count = 3
    result.remaining_issues_count = 1
    return result


class TestStreamingResultHandler:
    """Tests for StreamingResultHandler class."""

    def test_init_sets_output_format(self) -> None:
        """Handler stores output format."""
        handler = StreamingResultHandler(output_format="json", action=Action.CHECK)
        assert_that(handler.output_format).is_equal_to("json")

    def test_init_sets_action(self) -> None:
        """Handler stores action."""
        handler = StreamingResultHandler(output_format="grid", action=Action.FIX)
        assert_that(handler.action).is_equal_to(Action.FIX)

    def test_post_init_initializes_totals(self) -> None:
        """Handler initializes totals dictionary."""
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        totals = handler.get_totals()

        assert_that(totals).contains_key("issues", "fixed", "remaining")
        assert_that(totals["issues"]).is_equal_to(0)

    def test_handle_result_updates_totals(
        self,
        mock_tool_result: ToolResult,
    ) -> None:
        """Handle result updates totals.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(mock_tool_result)

        totals = handler.get_totals()
        assert_that(totals["tools_run"]).is_equal_to(1)
        assert_that(totals["issues"]).is_equal_to(2)

    def test_handle_result_tracks_failures(
        self,
        mock_tool_result_with_issues: ToolResult,
    ) -> None:
        """Handle result tracks failed tools.

        Args:
            mock_tool_result_with_issues: Fixture providing a failed ToolResult.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(mock_tool_result_with_issues)

        totals = handler.get_totals()
        assert_that(totals["tools_failed"]).is_equal_to(1)

    def test_handle_result_tracks_fix_counts(
        self,
        mock_fix_result: ToolResult,
    ) -> None:
        """Handle result tracks fix counts for FIX action.

        Args:
            mock_fix_result: Fixture providing a ToolResult with fix counts.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.FIX)
        handler.handle_result(mock_fix_result)

        totals = handler.get_totals()
        assert_that(totals["fixed"]).is_equal_to(3)
        assert_that(totals["remaining"]).is_equal_to(1)

    def test_handle_result_buffers_results(
        self,
        mock_tool_result: ToolResult,
    ) -> None:
        """Handle result buffers results.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(mock_tool_result)

        results = handler.get_results()
        assert_that(results).is_length(1)
        assert_that(results[0].name).is_equal_to("test_tool")

    def test_get_exit_code_returns_zero_on_success(self) -> None:
        """Get exit code returns 0 when all tools pass."""
        # Create a successful result with no issues
        success_result = ToolResult(
            name="test_tool",
            success=True,
            issues_count=0,
        )
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(success_result)

        assert_that(handler.get_exit_code()).is_equal_to(0)

    def test_get_exit_code_returns_one_on_failure(
        self,
        mock_tool_result_with_issues: ToolResult,
    ) -> None:
        """Get exit code returns 1 when tools fail.

        Args:
            mock_tool_result_with_issues: Fixture providing a failed ToolResult.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(mock_tool_result_with_issues)

        assert_that(handler.get_exit_code()).is_equal_to(1)

    def test_get_exit_code_returns_one_on_issues(
        self,
        mock_tool_result: ToolResult,
    ) -> None:
        """Get exit code returns 1 when issues found in check mode.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        handler = StreamingResultHandler(output_format="grid", action=Action.CHECK)
        handler.handle_result(mock_tool_result)  # Has 2 issues

        assert_that(handler.get_exit_code()).is_equal_to(1)

    def test_get_exit_code_fix_mode_checks_remaining(self) -> None:
        """Get exit code in FIX mode checks remaining issues."""
        result = ToolResult(name="test", success=True, issues_count=0)
        result.remaining_issues_count = 2

        handler = StreamingResultHandler(output_format="grid", action=Action.FIX)
        handler.handle_result(result)

        assert_that(handler.get_exit_code()).is_equal_to(1)


class TestStreamingResultHandlerContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_opens_file(self) -> None:
        """Context manager opens output file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            handler = StreamingResultHandler(
                output_format="jsonl",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                assert_that(handler._file_handle).is_not_none()
        finally:
            Path(temp_path).unlink()

    def test_context_manager_closes_file(self) -> None:
        """Context manager closes output file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            handler = StreamingResultHandler(
                output_format="jsonl",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                file_handle = handler._file_handle
            # After context, file should be closed
            assert_that(file_handle).is_not_none()
            assert file_handle is not None  # for mypy
            assert_that(file_handle.closed).is_true()
        finally:
            Path(temp_path).unlink()

    def test_json_format_writes_array_brackets(self) -> None:
        """JSON format writes array brackets."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            handler = StreamingResultHandler(
                output_format="json",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                pass

            content = Path(temp_path).read_text()
            assert_that(content).starts_with("[")
            assert_that(content).ends_with("]")
        finally:
            Path(temp_path).unlink()

    def test_handles_file_open_error(self) -> None:
        """Handler handles file open errors gracefully."""
        handler = StreamingResultHandler(
            output_format="jsonl",
            action=Action.CHECK,
            output_file="/nonexistent/directory/file.json",
        )
        # Should not raise
        with handler:
            assert_that(handler._file_handle).is_none()


class TestStreamingResultHandlerJSONL:
    """Tests for JSONL output format."""

    def test_writes_jsonl_format(self, mock_tool_result: ToolResult) -> None:
        """Handler writes JSONL format.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
            temp_path = f.name

        try:
            handler = StreamingResultHandler(
                output_format="jsonl",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                handler.handle_result(mock_tool_result)

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert_that(lines).is_length(1)

            data = json.loads(lines[0])
            assert_that(data["tool"]).is_equal_to("test_tool")
            assert_that(data["success"]).is_true()
        finally:
            Path(temp_path).unlink()

    def test_writes_multiple_jsonl_lines(self) -> None:
        """Handler writes multiple JSONL lines."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
            temp_path = f.name

        try:
            result1 = ToolResult(name="tool1", success=True, issues_count=0)
            result2 = ToolResult(name="tool2", success=True, issues_count=1)

            handler = StreamingResultHandler(
                output_format="jsonl",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                handler.handle_result(result1)
                handler.handle_result(result2)

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert_that(lines).is_length(2)

            assert_that(json.loads(lines[0])["tool"]).is_equal_to("tool1")
            assert_that(json.loads(lines[1])["tool"]).is_equal_to("tool2")
        finally:
            Path(temp_path).unlink()


class TestStreamingResultHandlerJSON:
    """Tests for JSON array output format."""

    def test_writes_json_array_format(self, mock_tool_result: ToolResult) -> None:
        """Handler writes JSON array format.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            handler = StreamingResultHandler(
                output_format="json",
                action=Action.CHECK,
                output_file=temp_path,
            )
            with handler:
                handler.handle_result(mock_tool_result)

            content = Path(temp_path).read_text()
            data = json.loads(content)
            assert_that(data).is_instance_of(list)
            assert_that(data).is_length(1)
            assert_that(data[0]["tool"]).is_equal_to("test_tool")
        finally:
            Path(temp_path).unlink()


class TestResultToDict:
    """Tests for _result_to_dict method."""

    def test_includes_basic_fields(self, mock_tool_result: ToolResult) -> None:
        """Result dict includes basic fields.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        handler = StreamingResultHandler(output_format="json", action=Action.CHECK)
        data = handler._result_to_dict(mock_tool_result)

        assert_that(data).contains_key("tool", "success", "issues_count")
        assert_that(data["tool"]).is_equal_to("test_tool")
        assert_that(data["success"]).is_true()
        assert_that(data["issues_count"]).is_equal_to(2)

    def test_includes_output_when_present(self, mock_tool_result: ToolResult) -> None:
        """Result dict includes output when present.

        Args:
            mock_tool_result: Fixture providing a mock ToolResult.
        """
        handler = StreamingResultHandler(output_format="json", action=Action.CHECK)
        data = handler._result_to_dict(mock_tool_result)

        assert_that(data).contains_key("output")
        assert_that(data["output"]).is_equal_to("Test output")

    def test_excludes_output_when_none(self) -> None:
        """Result dict excludes output when None."""
        result = ToolResult(name="test", success=True, issues_count=0, output=None)
        handler = StreamingResultHandler(output_format="json", action=Action.CHECK)
        data = handler._result_to_dict(result)

        assert_that(data).does_not_contain_key("output")

    def test_includes_fix_counts(self, mock_fix_result: ToolResult) -> None:
        """Result dict includes fix counts when present.

        Args:
            mock_fix_result: Fixture providing a ToolResult with fix counts.
        """
        handler = StreamingResultHandler(output_format="json", action=Action.FIX)
        data = handler._result_to_dict(mock_fix_result)

        assert_that(data).contains_key("fixed_issues_count", "remaining_issues_count")
        assert_that(data["fixed_issues_count"]).is_equal_to(3)
        assert_that(data["remaining_issues_count"]).is_equal_to(1)

    def test_includes_issues_list(
        self,
        mock_tool_result_with_issues: ToolResult,
    ) -> None:
        """Result dict includes issues list when present.

        Args:
            mock_tool_result_with_issues: Fixture providing a failed ToolResult.
        """
        handler = StreamingResultHandler(output_format="json", action=Action.CHECK)
        data = handler._result_to_dict(mock_tool_result_with_issues)

        assert_that(data).contains_key("issues")
        assert_that(data["issues"]).is_length(1)
        assert_that(data["issues"][0]["file"]).is_equal_to("test.py")
        assert_that(data["issues"][0]["line"]).is_equal_to(10)


class TestCreateStreamingHandler:
    """Tests for create_streaming_handler function."""

    def test_creates_handler_with_format(self) -> None:
        """Create handler with specified format."""
        handler = create_streaming_handler("json", Action.CHECK)

        assert_that(handler.output_format).is_equal_to("json")

    def test_creates_handler_with_action(self) -> None:
        """Create handler with specified action."""
        handler = create_streaming_handler("grid", Action.FIX)

        assert_that(handler.action).is_equal_to(Action.FIX)

    def test_creates_handler_with_output_file(self) -> None:
        """Create handler with output file."""
        handler = create_streaming_handler("json", Action.CHECK, "/tmp/output.json")

        assert_that(handler.output_file).is_equal_to("/tmp/output.json")

    def test_creates_handler_without_output_file(self) -> None:
        """Create handler without output file."""
        handler = create_streaming_handler("grid", Action.CHECK)

        assert_that(handler.output_file).is_none()
