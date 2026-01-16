"""Unit tests for sqlfluff plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.parsers.sqlfluff.sqlfluff_parser import parse_sqlfluff_output
from lintro.tools.definitions.sqlfluff import (
    SQLFLUFF_DEFAULT_FORMAT,
    SQLFLUFF_DEFAULT_TIMEOUT,
    SqlfluffPlugin,
)

if TYPE_CHECKING:
    pass


# Fixtures


@pytest.fixture
def sqlfluff_plugin() -> SqlfluffPlugin:
    """Provide a SqlfluffPlugin instance for testing.

    Returns:
        A SqlfluffPlugin instance with mocked verify_tool_version.
    """
    with patch(
        "lintro.plugins.base.verify_tool_version",
        return_value=None,
    ):
        return SqlfluffPlugin()


# Tests for default option values


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", SQLFLUFF_DEFAULT_TIMEOUT),
        ("dialect", None),
        ("exclude_rules", None),
        ("rules", None),
        ("templater", None),
    ],
    ids=[
        "timeout_equals_default",
        "dialect_is_none",
        "exclude_rules_is_none",
        "rules_is_none",
        "templater_is_none",
    ],
)
def test_default_options_values(
    sqlfluff_plugin: SqlfluffPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        sqlfluff_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)


# Tests for SqlfluffPlugin.set_options method - valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("dialect", "postgres"),
        ("dialect", "mysql"),
        ("dialect", "bigquery"),
        ("dialect", "snowflake"),
        ("exclude_rules", ["L001"]),
        ("exclude_rules", ["L001", "L002"]),
        ("rules", ["L002"]),
        ("rules", ["L002", "L003"]),
        ("templater", "jinja"),
        ("templater", "raw"),
        ("templater", "python"),
    ],
    ids=[
        "dialect_postgres",
        "dialect_mysql",
        "dialect_bigquery",
        "dialect_snowflake",
        "exclude_rules_single",
        "exclude_rules_multiple",
        "rules_single",
        "rules_multiple",
        "templater_jinja",
        "templater_raw",
        "templater_python",
    ],
)
def test_set_options_valid(
    sqlfluff_plugin: SqlfluffPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    sqlfluff_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(sqlfluff_plugin.options.get(option_name)).is_equal_to(option_value)


# Tests for SqlfluffPlugin.set_options method - invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("dialect", 123, "dialect must be a string"),
        ("dialect", ["postgres"], "dialect must be a string"),
        ("exclude_rules", "L001", "exclude_rules must be a list"),
        ("exclude_rules", 123, "exclude_rules must be a list"),
        ("rules", "L002", "rules must be a list"),
        ("rules", 123, "rules must be a list"),
        ("templater", 123, "templater must be a string"),
        ("templater", ["jinja"], "templater must be a string"),
    ],
    ids=[
        "invalid_dialect_int",
        "invalid_dialect_list",
        "invalid_exclude_rules_str",
        "invalid_exclude_rules_int",
        "invalid_rules_str",
        "invalid_rules_int",
        "invalid_templater_int",
        "invalid_templater_list",
    ],
)
def test_set_options_invalid_type(
    sqlfluff_plugin: SqlfluffPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
        option_name: The name of the option being tested.
        invalid_value: An invalid value for the option.
        error_match: Pattern expected in the error message.
    """
    with pytest.raises(ValueError, match=error_match):
        sqlfluff_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


# Tests for SqlfluffPlugin._build_lint_command method


def test_build_lint_command_basic(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build basic lint command without extra options.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("sqlfluff")
    assert_that(cmd).contains("lint")
    assert_that(cmd).contains("--format")
    assert_that(cmd).contains(SQLFLUFF_DEFAULT_FORMAT)
    assert_that(cmd).contains("test.sql")


def test_build_lint_command_with_dialect(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build lint command with dialect option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(dialect="postgres")
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("--dialect")
    dialect_idx = cmd.index("--dialect")
    assert_that(cmd[dialect_idx + 1]).is_equal_to("postgres")


def test_build_lint_command_with_exclude_rules(
    sqlfluff_plugin: SqlfluffPlugin,
) -> None:
    """Build lint command with exclude_rules option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(exclude_rules=["L001", "L002"])
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("--exclude-rules")
    # Each rule should have its own --exclude-rules flag
    exclude_count = cmd.count("--exclude-rules")
    assert_that(exclude_count).is_equal_to(2)


def test_build_lint_command_with_rules(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build lint command with rules option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(rules=["L002", "L003"])
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("--rules")
    # Each rule should have its own --rules flag
    rules_count = cmd.count("--rules")
    assert_that(rules_count).is_equal_to(2)


def test_build_lint_command_with_templater(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build lint command with templater option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(templater="jinja")
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("--templater")
    templater_idx = cmd.index("--templater")
    assert_that(cmd[templater_idx + 1]).is_equal_to("jinja")


def test_build_lint_command_with_all_options(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build lint command with all options set.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(
        dialect="postgres",
        exclude_rules=["L001"],
        rules=["L002"],
        templater="jinja",
    )
    cmd = sqlfluff_plugin._build_lint_command(files=["test.sql"])

    assert_that(cmd).contains("--dialect")
    assert_that(cmd).contains("--exclude-rules")
    assert_that(cmd).contains("--rules")
    assert_that(cmd).contains("--templater")
    assert_that(cmd).contains("test.sql")


def test_build_lint_command_multiple_files(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build lint command with multiple files.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    cmd = sqlfluff_plugin._build_lint_command(files=["test1.sql", "test2.sql"])

    assert_that(cmd).contains("test1.sql")
    assert_that(cmd).contains("test2.sql")


# Tests for SqlfluffPlugin._build_fix_command method


def test_build_fix_command_basic(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build basic fix command without extra options.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("sqlfluff")
    assert_that(cmd).contains("fix")
    assert_that(cmd).contains("--force")
    assert_that(cmd).contains("test.sql")


def test_build_fix_command_with_dialect(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build fix command with dialect option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(dialect="mysql")
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("--dialect")
    dialect_idx = cmd.index("--dialect")
    assert_that(cmd[dialect_idx + 1]).is_equal_to("mysql")


def test_build_fix_command_with_exclude_rules(
    sqlfluff_plugin: SqlfluffPlugin,
) -> None:
    """Build fix command with exclude_rules option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(exclude_rules=["L001"])
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("--exclude-rules")


def test_build_fix_command_with_rules(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build fix command with rules option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(rules=["L002"])
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("--rules")


def test_build_fix_command_with_templater(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build fix command with templater option.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(templater="raw")
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("--templater")
    templater_idx = cmd.index("--templater")
    assert_that(cmd[templater_idx + 1]).is_equal_to("raw")


def test_build_fix_command_with_all_options(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Build fix command with all options set.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    sqlfluff_plugin.set_options(
        dialect="bigquery",
        exclude_rules=["L001"],
        rules=["L002"],
        templater="python",
    )
    cmd = sqlfluff_plugin._build_fix_command(files=["test.sql"])

    assert_that(cmd).contains("--dialect")
    assert_that(cmd).contains("--exclude-rules")
    assert_that(cmd).contains("--rules")
    assert_that(cmd).contains("--templater")
    assert_that(cmd).contains("--force")
    assert_that(cmd).contains("test.sql")


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


def test_check_with_timeout(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

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
            side_effect=subprocess.TimeoutExpired(
                cmd=["sqlfluff"],
                timeout=SQLFLUFF_DEFAULT_TIMEOUT,
            ),
        ):
            result = sqlfluff_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()


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


def test_check_with_empty_output(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Check handles empty output correctly.

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
            result = sqlfluff_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


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


def test_fix_with_timeout(
    sqlfluff_plugin: SqlfluffPlugin,
    tmp_path: Path,
) -> None:
    """Fix handles timeout correctly.

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
            side_effect=subprocess.TimeoutExpired(
                cmd=["sqlfluff"],
                timeout=SQLFLUFF_DEFAULT_TIMEOUT,
            ),
        ):
            result = sqlfluff_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_false()


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


# Tests for output parsing


def test_parse_sqlfluff_output_single_issue() -> None:
    """Parse single issue from sqlfluff output."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case.",
                    "name": "capitalisation.keywords"
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.sql")
    assert_that(issues[0].line).is_equal_to(1)
    assert_that(issues[0].code).is_equal_to("L010")
    assert_that(issues[0].message).contains("Keywords must be upper case")


def test_parse_sqlfluff_output_multiple_issues() -> None:
    """Parse multiple issues from sqlfluff output."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case."
                },
                {
                    "start_line_no": 2,
                    "start_line_pos": 5,
                    "code": "L011",
                    "description": "Implicit aliasing of columns."
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].code).is_equal_to("L010")
    assert_that(issues[1].code).is_equal_to("L011")


def test_parse_sqlfluff_output_multiple_files() -> None:
    """Parse issues from multiple files."""
    output = """[
        {
            "filepath": "test1.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case."
                }
            ]
        },
        {
            "filepath": "test2.sql",
            "violations": [
                {
                    "start_line_no": 3,
                    "start_line_pos": 10,
                    "code": "L014",
                    "description": "Inconsistent capitalisation."
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("test1.sql")
    assert_that(issues[1].file).is_equal_to("test2.sql")


def test_parse_sqlfluff_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_sqlfluff_output("")

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_empty_array() -> None:
    """Parse empty array returns empty list."""
    issues = parse_sqlfluff_output("[]")

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_no_violations() -> None:
    """Parse output with no violations returns empty list."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": []
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_invalid_json() -> None:
    """Parse invalid JSON returns empty list."""
    issues = parse_sqlfluff_output("not valid json")

    assert_that(issues).is_empty()


# Tests for plugin definition


def test_plugin_definition_name(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Plugin definition has correct name.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    assert_that(sqlfluff_plugin.definition.name).is_equal_to("sqlfluff")


def test_plugin_definition_can_fix(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Plugin definition indicates it can fix issues.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    assert_that(sqlfluff_plugin.definition.can_fix).is_true()


def test_plugin_definition_file_patterns(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Plugin definition has correct file patterns.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    assert_that(sqlfluff_plugin.definition.file_patterns).contains("*.sql")


def test_plugin_definition_native_configs(sqlfluff_plugin: SqlfluffPlugin) -> None:
    """Plugin definition has correct native config files.

    Args:
        sqlfluff_plugin: The SqlfluffPlugin instance to test.
    """
    assert_that(sqlfluff_plugin.definition.native_configs).contains(".sqlfluff")
    assert_that(sqlfluff_plugin.definition.native_configs).contains("pyproject.toml")
