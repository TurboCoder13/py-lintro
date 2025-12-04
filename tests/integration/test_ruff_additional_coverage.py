"""Additional test coverage for Ruff tool changes."""

import os
import tempfile

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_ruff import RuffTool


@pytest.fixture(autouse=True)
def set_lintro_test_mode_env():
    """Set LINTRO_TEST_MODE=1 for all tests in this module.

    Yields:
        None: This fixture is used for its side effect only.
    """
    old = os.environ.get("LINTRO_TEST_MODE")
    os.environ["LINTRO_TEST_MODE"] = "1"
    yield
    if old is not None:
        os.environ["LINTRO_TEST_MODE"] = old
    else:
        del os.environ["LINTRO_TEST_MODE"]


@pytest.fixture
def ruff_tool():
    """Create a RuffTool instance for testing.

    Returns:
        RuffTool: A configured RuffTool instance.
    """
    # Disable Lintro config injection for these unit tests
    # so we can verify CLI argument building behavior
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    yield RuffTool()
    del os.environ["LINTRO_SKIP_CONFIG_INJECTION"]


@pytest.fixture
def ruff_clean_file():
    """Return the path to the static Ruff-clean file for testing.

    Yields:
        str: Path to the static ruff_clean.py file.
    """
    yield os.path.abspath("test_samples/ruff_clean.py")


@pytest.fixture
def ruff_violation_file():
    """Copy the ruff_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary ruff_violations.py file.
    """
    import shutil

    src = os.path.abspath("test_samples/ruff_violations.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "ruff_violations.py")
        shutil.copy(src, dst)
        yield dst


class TestRuffToolAdditionalCoverage:
    """Additional test cases for RuffTool covering recent changes."""

    def test_environment_variable_unsafe_fixes_override(self, monkeypatch) -> None:
        """Test that RUFF_UNSAFE_FIXES environment variable overrides unsafe_fixes.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        # Test various truthy values
        for env_value in ("true", "1", "yes", "on", "TRUE", "Yes"):
            monkeypatch.setenv("RUFF_UNSAFE_FIXES", env_value)
            tool = RuffTool()
            assert_that(tool.options["unsafe_fixes"]).is_true()

        # Test falsy values
        for env_value in ("false", "0", "no", "off", "", "invalid"):
            monkeypatch.setenv("RUFF_UNSAFE_FIXES", env_value)
            tool = RuffTool()
            assert_that(tool.options["unsafe_fixes"]).is_false()

        # Test when environment variable is not set
        monkeypatch.delenv("RUFF_UNSAFE_FIXES", raising=False)
        tool = RuffTool()
        assert_that(tool.options["unsafe_fixes"]).is_false()

    def test_set_options_string_to_list_conversion(self, ruff_tool) -> None:
        """Test that set_options converts string parameters to lists.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        # Test string conversion for select
        ruff_tool.set_options(select="E")
        assert_that(ruff_tool.options["select"]).is_equal_to(["E"])

        # Test string conversion for ignore
        ruff_tool.set_options(ignore="E501")
        assert_that(ruff_tool.options["ignore"]).is_equal_to(["E501"])

        # Test string conversion for extend_select
        ruff_tool.set_options(extend_select="F")
        assert_that(ruff_tool.options["extend_select"]).is_equal_to(["F"])

        # Test string conversion for extend_ignore
        ruff_tool.set_options(extend_ignore="W")
        assert_that(ruff_tool.options["extend_ignore"]).is_equal_to(["W"])

        # Test that lists remain unchanged
        ruff_tool.set_options(select=["E", "F"])
        assert_that(ruff_tool.options["select"]).is_equal_to(["E", "F"])

    def test_set_options_invalid_extend_select(self, ruff_tool) -> None:
        """Test setting invalid extend_select option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="extend_select must be a string or list"):
            ruff_tool.set_options(extend_select=123)

    def test_set_options_invalid_extend_ignore(self, ruff_tool) -> None:
        """Test setting invalid extend_ignore option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="extend_ignore must be a string or list"):
            ruff_tool.set_options(extend_ignore=123)

    def test_fix_success_logic_no_initial_issues(
        self,
        ruff_tool,
        ruff_clean_file,
    ) -> None:
        """Test fix success logic when there are no initial issues.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_clean_file: Path to the static clean Python file.
        """
        result = ruff_tool.fix([ruff_clean_file])
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.initial_issues_count).is_equal_to(0)
        assert_that(result.fixed_issues_count).is_equal_to(0)
        assert_that(result.remaining_issues_count).is_equal_to(0)

    def test_fix_success_logic_with_remaining_issues(
        self,
        ruff_tool,
        ruff_violation_file,
    ) -> None:
        """Test fix success logic when there are remaining unfixable issues.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        # Use a configuration that will leave some issues unfixed
        ruff_tool.set_options(select=["E"], unsafe_fixes=False)
        result = ruff_tool.fix([ruff_violation_file])

        # Success should be False if there are remaining issues
        if result.remaining_issues_count > 0:
            assert_that(result.success).is_false()
        else:
            assert_that(result.success).is_true()

    def test_fix_empty_paths(self, ruff_tool) -> None:
        """Test fixing with empty paths.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        result = ruff_tool.fix([])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_true()
        assert_that(result.output).is_equal_to("No files to fix.")
        assert_that(result.issues_count).is_equal_to(0)

    def test_fix_nonexistent_file(self, ruff_tool) -> None:
        """Test fixing a nonexistent file.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(FileNotFoundError):
            ruff_tool.fix(["/nonexistent/file.py"])

    def test_build_check_command_with_unsafe_fixes(self, ruff_tool) -> None:
        """Test building check command with unsafe fixes.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(unsafe_fixes=True)
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)
        assert_that(cmd).contains("--unsafe-fixes")

    def test_build_check_command_with_show_fixes(self, ruff_tool) -> None:
        """Test building check command with show fixes.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(show_fixes=True)
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)
        assert_that(cmd).contains("--show-fixes")

    def test_build_check_command_with_fix_only(self, ruff_tool) -> None:
        """Test building check command with fix only.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(fix_only=True)
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)
        assert_that(cmd).contains("--fix-only")

    def test_build_check_command_with_target_version(self, ruff_tool) -> None:
        """Test building check command with target version.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(target_version="py39")
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        assert_that(cmd).contains("--target-version")
        assert_that(cmd).contains("py39")

    def test_build_format_command_with_target_version(self, ruff_tool) -> None:
        """Test building format command with target version.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(target_version="py39")
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files)
        assert_that(cmd).contains("--target-version")
        assert_that(cmd).contains("py39")

    def test_e501_auto_inclusion_when_selecting_e_family(self, ruff_tool) -> None:
        """Test that E501 is automatically included when selecting E family.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["E"])
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        # Should contain both --select E and --extend-select E501
        assert_that(cmd).contains("--select")
        assert_that(cmd).contains("E")
        assert_that(cmd).contains("--extend-select")
        assert_that(cmd).contains("E501")

    def test_e501_not_included_when_explicitly_ignored(self, ruff_tool) -> None:
        """Test that E501 is not included when explicitly ignored.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["E"], ignore=["E501"])
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        # Should contain --select E and --ignore E501, but not --extend-select E501
        assert_that(cmd).contains("--select")
        assert_that(cmd).contains("E")
        assert_that(cmd).contains("--ignore")
        assert_that(cmd).contains("E501")
        # E501 should not be in extend-select since it's ignored
        extend_select_parts = [
            part for part in cmd if part.startswith("--extend-select")
        ]
        if extend_select_parts:
            assert_that(extend_select_parts[0]).does_not_contain("E501")

    def test_e501_not_included_when_explicitly_selected(self, ruff_tool) -> None:
        """Test that E501 is not included in extend-select when explicitly selected.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["E", "E501"])
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        # Should contain --select E,E501 but not --extend-select E501
        assert_that(cmd).contains("--select")
        assert_that(cmd).contains("E,E501")
        # E501 should not be in extend-select since it's already selected
        extend_select_parts = [
            part for part in cmd if part.startswith("--extend-select")
        ]
        if extend_select_parts:
            assert_that(extend_select_parts[0]).does_not_contain("E501")

    def test_format_check_disabled(self, ruff_tool, ruff_violation_file) -> None:
        """Test that format check can be disabled.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        ruff_tool.set_options(format_check=False)
        result = ruff_tool.check([ruff_violation_file])

        # Should only report linting issues, not formatting issues
        assert_that(isinstance(result, ToolResult)).is_true()
        # Format issues should not be included when format_check is False
        format_issues = [
            issue
            for issue in result.issues or []
            if hasattr(issue, "code") and issue.code == "FORMAT"
        ]
        assert_that(len(format_issues)).is_equal_to(0)

    def test_format_disabled_during_fix(self, ruff_tool, ruff_violation_file) -> None:
        """Test that format can be disabled during fix.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        ruff_tool.set_options(format=False, lint_fix=True)
        result = ruff_tool.fix([ruff_violation_file])

        assert_that(isinstance(result, ToolResult)).is_true()
        # Should still work but only apply lint fixes, not formatting

    def test_lint_fix_disabled_during_fix(self, ruff_tool, ruff_violation_file) -> None:
        """Test that lint fix can be disabled during fix.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        ruff_tool.set_options(format=True, lint_fix=False)
        result = ruff_tool.fix([ruff_violation_file])

        assert_that(isinstance(result, ToolResult)).is_true()
        # Should still work but only apply formatting, not lint fixes

    def test_check_empty_paths(self, ruff_tool) -> None:
        """Test checking with empty paths.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        result = ruff_tool.check([])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_true()
        assert_that(result.output).is_equal_to("No files to check.")
        assert_that(result.issues_count).is_equal_to(0)

    def test_check_nonexistent_file(self, ruff_tool) -> None:
        """Test checking a nonexistent file.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(FileNotFoundError):
            ruff_tool.check(["/nonexistent/file.py"])

    def test_build_check_command_with_extend_ignore(self, ruff_tool) -> None:
        """Test building check command with extend ignore.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(extend_ignore=["W"])
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        assert_that(cmd).contains("--extend-ignore")
        assert_that(cmd).contains("W")

    def test_build_check_command_with_extend_select(self, ruff_tool) -> None:
        """Test building check command with extend select.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(extend_select=["F"])
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        assert_that(cmd).contains("--extend-select")
        assert_that(cmd).contains("F")

    def test_build_check_command_with_line_length(self, ruff_tool) -> None:
        """Test building check command with line length.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(line_length=100)
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        assert_that(cmd).contains("--line-length")
        assert_that(cmd).contains("100")

    def test_build_format_command_with_line_length(self, ruff_tool) -> None:
        """Test building format command with line length.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(line_length=100)
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files)
        assert_that(cmd).contains("--line-length")
        assert_that(cmd).contains("100")

    def test_set_options_invalid_target_version(self, ruff_tool) -> None:
        """Test setting invalid target version.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="target_version must be a string"):
            ruff_tool.set_options(target_version=123)

    def test_set_options_invalid_fix_only(self, ruff_tool) -> None:
        """Test setting invalid fix_only option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="fix_only must be a boolean"):
            ruff_tool.set_options(fix_only="true")

    def test_set_options_invalid_unsafe_fixes(self, ruff_tool) -> None:
        """Test setting invalid unsafe_fixes option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="unsafe_fixes must be a boolean"):
            ruff_tool.set_options(unsafe_fixes="true")

    def test_set_options_invalid_show_fixes(self, ruff_tool) -> None:
        """Test setting invalid show_fixes option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="show_fixes must be a boolean"):
            ruff_tool.set_options(show_fixes="true")

    def test_set_options_invalid_format(self, ruff_tool) -> None:
        """Test setting invalid format option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="format must be a boolean"):
            ruff_tool.set_options(format="true")

    def test_set_options_invalid_format_check(self, ruff_tool) -> None:
        """Test setting invalid format_check option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="format_check must be a boolean"):
            ruff_tool.set_options(format_check="true")
