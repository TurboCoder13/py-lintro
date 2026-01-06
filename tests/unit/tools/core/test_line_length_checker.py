"""Unit tests for the shared line length checker utility."""

import json
import subprocess
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.tools.core.line_length_checker import (
    LineLengthViolation,
    check_line_length_violations,
)


class TestLineLengthViolation:
    """Tests for the LineLengthViolation dataclass."""

    def test_default_code_is_e501(self) -> None:
        """Test that the default code is E501."""
        violation = LineLengthViolation(
            file="test.py",
            line=10,
            column=89,
            message="Line too long (100 > 88)",
        )
        assert_that(violation.code).is_equal_to("E501")

    def test_all_fields_set(self) -> None:
        """Test creating a violation with all fields."""
        violation = LineLengthViolation(
            file="/path/to/file.py",
            line=42,
            column=100,
            message="Line too long (120 > 88)",
            code="E501",
        )
        assert_that(violation.file).is_equal_to("/path/to/file.py")
        assert_that(violation.line).is_equal_to(42)
        assert_that(violation.column).is_equal_to(100)
        assert_that(violation.message).is_equal_to("Line too long (120 > 88)")
        assert_that(violation.code).is_equal_to("E501")


class TestCheckLineLengthViolations:
    """Tests for the check_line_length_violations function."""

    def test_empty_files_returns_empty_list(self) -> None:
        """Test that empty file list returns empty violations."""
        result = check_line_length_violations(files=[])
        assert_that(result).is_empty()

    @patch("shutil.which")
    def test_ruff_not_available_returns_empty(self, mock_which: MagicMock) -> None:
        """Test that missing ruff returns empty violations without error.

        Args:
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = None

        result = check_line_length_violations(files=["test.py"])

        assert_that(result).is_empty()
        mock_which.assert_called_once_with("ruff")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_successful_detection(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test successful detection of E501 violations.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"

        # Simulate Ruff JSON output with E501 violation
        ruff_output = json.dumps(
            [
                {
                    "filename": "/path/to/file.py",
                    "location": {"row": 10, "column": 89},
                    "message": "Line too long (100 > 88)",
                    "code": "E501",
                },
            ],
        )
        mock_run.return_value = MagicMock(
            stdout=ruff_output,
            returncode=1,  # Ruff returns 1 when issues found
        )

        result = check_line_length_violations(
            files=["file.py"],
            cwd="/path/to",
        )

        assert_that(result).is_length(1)
        assert_that(result[0].file).is_equal_to("/path/to/file.py")
        assert_that(result[0].line).is_equal_to(10)
        assert_that(result[0].column).is_equal_to(89)
        assert_that(result[0].message).is_equal_to("Line too long (100 > 88)")
        assert_that(result[0].code).is_equal_to("E501")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_custom_line_length(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that custom line_length is passed to ruff.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        check_line_length_violations(
            files=["test.py"],
            line_length=100,
        )

        # Verify --line-length was passed
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert_that(cmd).contains("--line-length")
        assert_that(cmd).contains("100")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_timeout_returns_empty(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that timeout exception returns empty list gracefully.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["ruff"],
            timeout=30,
        )

        result = check_line_length_violations(files=["test.py"], timeout=30)

        assert_that(result).is_empty()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_json_parse_error_returns_empty(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that invalid JSON returns empty list gracefully.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.return_value = MagicMock(
            stdout="not valid json",
            returncode=1,
        )

        result = check_line_length_violations(files=["test.py"])

        assert_that(result).is_empty()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_empty_stdout_returns_empty(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that empty stdout returns empty list.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=0,
        )

        result = check_line_length_violations(files=["test.py"])

        assert_that(result).is_empty()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_file_not_found_returns_empty(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that FileNotFoundError returns empty list gracefully.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.side_effect = FileNotFoundError("ruff not found")

        result = check_line_length_violations(files=["test.py"])

        assert_that(result).is_empty()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_relative_paths_converted_to_absolute(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that relative file paths are converted to absolute.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        check_line_length_violations(
            files=["src/module.py", "tests/test_module.py"],
            cwd="/project",
        )

        # Verify absolute paths were passed
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert_that(cmd).contains("/project/src/module.py")
        assert_that(cmd).contains("/project/tests/test_module.py")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_old_ruff_json_format(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test compatibility with older Ruff JSON format (no location wrapper).

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"

        # Older Ruff format with row/column at top level
        ruff_output = json.dumps(
            [
                {
                    "filename": "/path/to/file.py",
                    "row": 15,
                    "column": 100,
                    "message": "Line too long (110 > 88)",
                    "code": "E501",
                },
            ],
        )
        mock_run.return_value = MagicMock(
            stdout=ruff_output,
            returncode=1,
        )

        result = check_line_length_violations(files=["file.py"], cwd="/path/to")

        assert_that(result).is_length(1)
        assert_that(result[0].line).is_equal_to(15)
        assert_that(result[0].column).is_equal_to(100)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_multiple_violations(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test handling multiple E501 violations.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"

        ruff_output = json.dumps(
            [
                {
                    "filename": "/path/file1.py",
                    "location": {"row": 10, "column": 89},
                    "message": "Line too long (100 > 88)",
                    "code": "E501",
                },
                {
                    "filename": "/path/file2.py",
                    "location": {"row": 25, "column": 89},
                    "message": "Line too long (150 > 88)",
                    "code": "E501",
                },
                {
                    "filename": "/path/file1.py",
                    "location": {"row": 50, "column": 89},
                    "message": "Line too long (200 > 88)",
                    "code": "E501",
                },
            ],
        )
        mock_run.return_value = MagicMock(
            stdout=ruff_output,
            returncode=1,
        )

        result = check_line_length_violations(files=["file1.py", "file2.py"])

        assert_that(result).is_length(3)
        assert_that([v.file for v in result]).contains(
            "/path/file1.py",
            "/path/file2.py",
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_command_includes_required_flags(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that the ruff command includes required flags.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        check_line_length_violations(files=["test.py"])

        call_args = mock_run.call_args
        cmd = call_args[0][0]

        # Verify essential flags
        assert_that(cmd).contains("check")
        assert_that(cmd).contains("--select")
        assert_that(cmd).contains("E501")
        assert_that(cmd).contains("--output-format")
        assert_that(cmd).contains("json")
        assert_that(cmd).contains("--no-cache")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generic_exception_returns_empty(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test that generic exceptions return empty list gracefully.

        Args:
            mock_run: Mock for subprocess.run function.
            mock_which: Mock for shutil.which function.
        """
        mock_which.return_value = "/usr/bin/ruff"
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = check_line_length_violations(files=["test.py"])

        assert_that(result).is_empty()
