"""Unit tests for sqlfluff plugin check and fix method execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.definitions.sqlfluff import SqlfluffPlugin

# Tests for SqlfluffPlugin.check method


def test_check_with_mocked_subprocess_success(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no issues found.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_query.sql"
    test_file.write_text("SELECT * FROM users;\n")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            sqlfluff_plugin,
            "_run_subprocess",
            return_value=(True, "[]"),
        ):
            result = sqlfluff_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_mocked_subprocess_issues(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when sqlfluff finds problems.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_query.sql"
    test_file.write_text("select * from users;\n")

    sqlfluff_output = """[
        {
            "filepath": "test_query.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "end_line_no": 1,
                    "end_line_pos": 6,
                    "code": "L010",
                    "description": "Keywords must be upper case.",
                    "name": "capitalisation.keywords"
                }
            ]
        }
    ]"""

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            sqlfluff_plugin,
            "_run_subprocess",
            return_value=(False, sqlfluff_output),
        ):
            result = sqlfluff_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


def test_check_with_no_sql_files(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no SQL files found.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_sql_file = tmp_path / "test.txt"
    non_sql_file.write_text("Not a SQL file")

    with patch.object(sqlfluff_plugin, "_verify_tool_version", return_value=None):
        result = sqlfluff_plugin.check([str(non_sql_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No")


# Tests for SqlfluffPlugin.fix method


def test_fix_with_mocked_subprocess_success(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when fixes applied.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_query.sql"
    test_file.write_text("select * from users;\n")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            sqlfluff_plugin,
            "_run_subprocess",
            return_value=(True, "Fixed 1 file(s)"),
        ):
            result = sqlfluff_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_fix_with_mocked_subprocess_no_changes(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when no changes needed.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    test_file = tmp_path / "test_query.sql"
    test_file.write_text("SELECT * FROM users;\n")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            sqlfluff_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = sqlfluff_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()


def test_fix_with_no_sql_files(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns success when no SQL files found.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        tmp_path: Temporary directory path for test files.
    """
    non_sql_file = tmp_path / "test.txt"
    non_sql_file.write_text("Not a SQL file")

    with patch.object(sqlfluff_plugin, "_verify_tool_version", return_value=None):
        result = sqlfluff_plugin.fix([str(non_sql_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.output).contains("No")
