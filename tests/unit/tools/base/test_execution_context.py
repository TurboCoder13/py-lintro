"""Unit tests for ExecutionContext and _prepare_execution."""

from __future__ import annotations

from typing import Never
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.tools.core.tool_base import BaseTool, ExecutionContext


class _TestTool(BaseTool):
    """Test tool for ExecutionContext tests."""

    name: str = "test_tool"
    description: str = "Test tool for unit tests"
    can_fix: bool = False
    config: ToolConfig = ToolConfig(
        priority=1,
        conflicts_with=[],
        file_patterns=["*.py"],
        tool_type=ToolType.LINTER,
    )

    def check(self, paths: list[str]) -> Never:  # type: ignore[override]
        raise NotImplementedError

    def fix(self, paths: list[str]) -> Never:  # type: ignore[override]
        raise NotImplementedError


class TestExecutionContext:
    """Tests for the ExecutionContext dataclass."""

    def test_default_values(self) -> None:
        """Test ExecutionContext default values."""
        ctx = ExecutionContext()

        assert_that(ctx.files).is_empty()
        assert_that(ctx.rel_files).is_empty()
        assert_that(ctx.cwd).is_none()
        assert_that(ctx.early_result).is_none()
        assert_that(ctx.timeout).is_equal_to(30)

    def test_should_skip_when_early_result_is_none(self) -> None:
        """Test should_skip returns False when no early_result."""
        ctx = ExecutionContext()

        assert_that(ctx.should_skip).is_false()

    def test_should_skip_when_early_result_is_set(self) -> None:
        """Test should_skip returns True when early_result is set."""
        early = ToolResult(
            name="test",
            success=True,
            output="No files",
            issues_count=0,
        )
        ctx = ExecutionContext(early_result=early)

        assert_that(ctx.should_skip).is_true()

    def test_all_fields_set(self) -> None:
        """Test ExecutionContext with all fields set."""
        early = ToolResult(
            name="test",
            success=True,
            output="Test",
            issues_count=0,
        )
        ctx = ExecutionContext(
            files=["/path/to/file.py"],
            rel_files=["file.py"],
            cwd="/path/to",
            early_result=early,
            timeout=60,
        )

        assert_that(ctx.files).is_equal_to(["/path/to/file.py"])
        assert_that(ctx.rel_files).is_equal_to(["file.py"])
        assert_that(ctx.cwd).is_equal_to("/path/to")
        assert_that(ctx.early_result).is_equal_to(early)
        assert_that(ctx.timeout).is_equal_to(60)


class TestPrepareExecution:
    """Tests for the _prepare_execution method."""

    @pytest.fixture
    def tool(self) -> _TestTool:
        """Create a test tool instance.

        Returns:
            _TestTool: Configured test tool instance.
        """
        return _TestTool(
            name="test_tool",
            description="Test tool for unit tests",
            can_fix=False,
        )

    def test_empty_paths_returns_early_result(self, tool: _TestTool) -> None:
        """Test that empty paths returns success with message."""
        ctx = tool._prepare_execution([])

        assert_that(ctx.should_skip).is_true()
        assert_that(ctx.early_result).is_not_none()
        assert_that(ctx.early_result.success).is_true()  # type: ignore[union-attr]
        assert_that(ctx.early_result.output).contains("No files")  # type: ignore[union-attr]
        assert_that(ctx.early_result.issues_count).is_equal_to(0)  # type: ignore[union-attr]

    @patch.object(_TestTool, "_verify_tool_version")
    def test_version_check_failure_returns_early(
        self,
        mock_verify: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test that version check failure returns early result."""
        version_error = ToolResult(
            name="test_tool",
            success=False,
            output="Version requirement not met",
            issues_count=1,
        )
        mock_verify.return_value = version_error

        ctx = tool._prepare_execution(["some/path"])

        assert_that(ctx.should_skip).is_true()
        assert_that(ctx.early_result).is_equal_to(version_error)

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_no_matching_files_returns_early(
        self,
        mock_walk: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test that no matching files returns early result."""
        mock_walk.return_value = []

        ctx = tool._prepare_execution(["some/path"])

        assert_that(ctx.should_skip).is_true()
        assert_that(ctx.early_result).is_not_none()
        assert_that(ctx.early_result.success).is_true()  # type: ignore[union-attr]
        assert_that(ctx.early_result.output).contains("No")  # type: ignore[union-attr]
        assert_that(ctx.early_result.output).contains("files")  # type: ignore[union-attr]

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch.object(_TestTool, "get_cwd")
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_successful_preparation(
        self,
        mock_walk: MagicMock,
        mock_cwd: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test successful execution context preparation."""
        mock_walk.return_value = ["/project/src/file.py", "/project/src/test.py"]
        mock_cwd.return_value = "/project/src"

        ctx = tool._prepare_execution(["/project/src"])

        assert_that(ctx.should_skip).is_false()
        assert_that(ctx.early_result).is_none()
        assert_that(ctx.files).is_equal_to(
            ["/project/src/file.py", "/project/src/test.py"],
        )
        assert_that(ctx.rel_files).is_equal_to(["file.py", "test.py"])
        assert_that(ctx.cwd).is_equal_to("/project/src")

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch.object(_TestTool, "get_cwd")
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_custom_timeout(
        self,
        mock_walk: MagicMock,
        mock_cwd: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test custom default_timeout is used."""
        mock_walk.return_value = ["/project/file.py"]
        mock_cwd.return_value = "/project"

        ctx = tool._prepare_execution(["/project"], default_timeout=120)

        assert_that(ctx.timeout).is_equal_to(120)

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch.object(_TestTool, "get_cwd")
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_timeout_from_options(
        self,
        mock_walk: MagicMock,
        mock_cwd: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test timeout from tool options takes precedence."""
        mock_walk.return_value = ["/project/file.py"]
        mock_cwd.return_value = "/project"
        tool.options["timeout"] = 90

        ctx = tool._prepare_execution(["/project"])

        assert_that(ctx.timeout).is_equal_to(90)

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_custom_file_patterns(
        self,
        mock_walk: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test custom file patterns are passed to walk_files_with_excludes."""
        mock_walk.return_value = []

        tool._prepare_execution(["/project"], file_patterns=["*.tsx", "*.ts"])

        # Verify custom patterns were passed
        call_kwargs = mock_walk.call_args.kwargs
        assert_that(call_kwargs["file_patterns"]).is_equal_to(["*.tsx", "*.ts"])

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_custom_exclude_patterns(
        self,
        mock_walk: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test custom exclude patterns are passed to walk_files_with_excludes."""
        mock_walk.return_value = []

        tool._prepare_execution(["/project"], exclude_patterns=["vendor/*", "dist/*"])

        # Verify custom excludes were passed
        call_kwargs = mock_walk.call_args.kwargs
        assert_that(call_kwargs["exclude_patterns"]).is_equal_to(["vendor/*", "dist/*"])

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_custom_no_files_message(
        self,
        mock_walk: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test custom no_files_message is used."""
        mock_walk.return_value = []

        ctx = tool._prepare_execution(
            ["/project"],
            no_files_message="No Python source files found.",
        )

        # When no files found, should still get "No ... files found to check"
        # from file type detection. Empty paths list uses custom message.
        assert_that(ctx.should_skip).is_true()
        assert_that(ctx.early_result).is_not_none()

    @patch.object(_TestTool, "_validate_paths", return_value=None)
    @patch.object(_TestTool, "_verify_tool_version", return_value=None)
    @patch.object(_TestTool, "get_cwd")
    @patch("lintro.tools.core.tool_base.walk_files_with_excludes")
    def test_files_with_no_cwd(
        self,
        mock_walk: MagicMock,
        mock_cwd: MagicMock,
        mock_verify: MagicMock,
        mock_validate: MagicMock,
        tool: _TestTool,
    ) -> None:
        """Test file paths when cwd is None."""
        mock_walk.return_value = ["/project/file.py"]
        mock_cwd.return_value = None

        ctx = tool._prepare_execution(["/project"])

        assert_that(ctx.cwd).is_none()
        # rel_files should equal absolute files when no cwd
        assert_that(ctx.rel_files).is_equal_to(["/project/file.py"])
