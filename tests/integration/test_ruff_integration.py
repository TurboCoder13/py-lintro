"""Integration tests for Ruff tool."""

import os
import shutil
import tempfile

import pytest

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
    return RuffTool()


@pytest.fixture
def ruff_violation_file():
    """Copy the ruff_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary ruff_violations.py file.
    """
    src = os.path.abspath("test_samples/ruff_violations.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "ruff_violations.py")
        shutil.copy(src, dst)
        yield dst


@pytest.fixture
def ruff_clean_file():
    """Return the path to the static Ruff-clean file for testing.

    Yields:
        str: Path to the static ruff_clean.py file.
    """
    yield os.path.abspath("test_samples/ruff_clean.py")


@pytest.fixture
def temp_python_file(request):
    """Create a temporary Python file with ruff violations.

    Args:
        request: Pytest request fixture for finalizer registration.

    Yields:
        str: Path to the temporary Python file with violations.
    """
    content = '''"""Test file with ruff violations."""

import sys,os
import json
from pathlib    import Path

def hello(name:str='World'):
    print(f'Hello, {name}!')
    unused_var = 42

if __name__=='__main__':
    hello()
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = f.name

    # Debug: print file path and contents
    print(f"[DEBUG] temp_python_file path: {file_path}")
    with open(file_path, "r") as debug_f:
        print("[DEBUG] temp_python_file contents:")
        print(debug_f.read())

    def cleanup():
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass

    request.addfinalizer(cleanup)
    yield file_path


class TestRuffTool:
    """Test cases for RuffTool."""

    def test_tool_initialization(self, ruff_tool):
        """Test that RuffTool initializes correctly.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert ruff_tool.name == "ruff"
        assert ruff_tool.can_fix is True
        assert "*.py" in ruff_tool.config.file_patterns
        assert "*.pyi" in ruff_tool.config.file_patterns

    def test_tool_priority(self, ruff_tool):
        """Test that RuffTool has high priority.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert ruff_tool.config.priority == 85

    def test_lint_check_clean_file(self, ruff_tool, ruff_clean_file):
        """Test Ruff lint check on a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_clean_file: Path to the static clean Python file.
        """
        ruff_tool.set_options(select=["E", "F"])
        result = ruff_tool.check([ruff_clean_file])
        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        assert result.success is True
        assert result.issues_count == 0

    def test_lint_check_violations(self, ruff_tool, ruff_violation_file):
        """Test Ruff lint check on a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        ruff_tool.set_options(select=["E", "F"])
        result = ruff_tool.check([ruff_violation_file])
        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        assert result.success is False
        assert result.issues_count > 0

    def test_check_nonexistent_file(self, ruff_tool):
        """Test checking a nonexistent file.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(FileNotFoundError):
            ruff_tool.check(["/nonexistent/file.py"])

    def test_check_empty_paths(self, ruff_tool):
        """Test checking with empty paths.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        result = ruff_tool.check([])

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == "No files to check."
        assert result.issues_count == 0

    def test_fix_with_violations(self, ruff_tool, temp_python_file):
        """Test fixing a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            temp_python_file: Temporary Python file with violations.
        """
        result = ruff_tool.fix([temp_python_file])

        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        # After fixing, the file should be improved
        assert result.output != "No fixes applied."

    def test_set_options_valid(self, ruff_tool):
        """Test setting valid options.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(
            select=["E", "F"],
            ignore=["E501"],
            line_length=88,
            target_version="py39",
            unsafe_fixes=True,
            format=False,
        )

        assert ruff_tool.options["select"] == ["E", "F"]
        assert ruff_tool.options["ignore"] == ["E501"]
        assert ruff_tool.options["line_length"] == 88
        assert ruff_tool.options["target_version"] == "py39"
        assert ruff_tool.options["unsafe_fixes"] is True
        assert ruff_tool.options["format"] is False

    def test_set_options_invalid_select(self, ruff_tool):
        """Test setting invalid select option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="select must be a list"):
            ruff_tool.set_options(select="E,F")

    def test_set_options_invalid_line_length(self, ruff_tool):
        """Test setting invalid line length.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="line_length must be an integer"):
            ruff_tool.set_options(line_length="88")

        with pytest.raises(ValueError, match="line_length must be positive"):
            ruff_tool.set_options(line_length=-1)

    def test_build_check_command_basic(self, ruff_tool):
        """Test building basic check command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        assert cmd[0] == "ruff"
        assert cmd[1] == "check"
        assert "--output-format" in cmd
        assert "json" in cmd
        assert "test.py" in cmd

    def test_build_check_command_with_fix(self, ruff_tool):
        """Test building check command with fix option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)

        assert "--fix" in cmd

    def test_build_check_command_with_options(self, ruff_tool):
        """Test building check command with various options.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(
            select=["E", "F"],
            ignore=["E501"],
            line_length=88,
        )

        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)

        assert "--select" in cmd
        assert "E,F" in cmd
        assert "--ignore" in cmd
        assert "E501" in cmd
        assert "--line-length" in cmd
        assert "88" in cmd

    def test_build_format_command_basic(self, ruff_tool):
        """Test building basic format command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files)

        assert cmd[0] == "ruff"
        assert cmd[1] == "format"
        assert "test.py" in cmd

    def test_build_format_command_check_only(self, ruff_tool):
        """Test building format command in check-only mode.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files, check_only=True)

        assert "--check" in cmd

    def test_check_reports_formatting_issues(self, ruff_tool, request):
        """Test that check reports formatting issues (not just lint issues).

        Args:
            ruff_tool: RuffTool fixture instance.
            request: Pytest request fixture for cleanup.
        """
        # Create a file with a formatting issue (e.g., trailing whitespace)
        content = "def foo():\n    return 42    \n"  # trailing whitespace
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        def cleanup():
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass

        request.addfinalizer(cleanup)
        ruff_tool.set_options(select=["E", "F"])  # Enable common rules
        # Manually run ruff format --check to see raw output
        import subprocess

        format_cmd = ["ruff", "format", "--check", file_path]
        proc = subprocess.run(format_cmd, capture_output=True, text=True)
        print("[DEBUG] ruff format --check stdout:")
        print(proc.stdout)
        print("[DEBUG] ruff format --check stderr:")
        print(proc.stderr)
        result = ruff_tool.check([file_path])
        assert isinstance(result, ToolResult)
        assert result.name == "ruff"
        assert result.success is False  # Should find a formatting issue
        assert result.issues_count > 0
        assert (
            "Would reformat" in result.output or "Formatting issues:" in result.output
        )

    def test_format_check_clean_file(self, ruff_tool, ruff_clean_file):
        """Test format check on a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_clean_file: Path to the static clean Python file.
        """
        result = ruff_tool.check([ruff_clean_file])
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.issues_count == 0
        assert "Formatting issues:" not in result.output

    def test_format_check_violations(self, ruff_tool, ruff_violation_file):
        """Test format check on a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        result = ruff_tool.check([ruff_violation_file])
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.issues_count > 0
        assert (
            "Formatting issues:" in result.output or "Would reformat" in result.output
        )

    def test_fmt_fixes_violations(self, ruff_tool, ruff_violation_file):
        """
        Test that applying format/fix to a file with violations results in a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        fix_result = ruff_tool.fix([ruff_violation_file])
        assert isinstance(fix_result, ToolResult)
        # After fixing, check that the file is now clean
        check_result = ruff_tool.check([ruff_violation_file])
        assert isinstance(check_result, ToolResult)
        assert check_result.success is True
        assert check_result.issues_count == 0
