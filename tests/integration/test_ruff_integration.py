"""Integration tests for Ruff tool."""

import contextlib
import os
import shutil
import tempfile

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_ruff import RuffTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


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
    content = (
        "# Test file with ruff violations\n\n"
        "import sys,os\n"
        "import json\n"
        "from pathlib    import Path\n\n"
        "def hello(name:str='World'):\n"
        "    print(f'Hello, {name}!')\n"
        "    unused_var = 42\n\n"
        "if __name__=='__main__':\n"
        "    hello()\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = f.name
    print(f"[DEBUG] temp_python_file path: {file_path}")
    with open(file_path) as debug_f:
        print("[DEBUG] temp_python_file contents:")
        print(debug_f.read())

    def cleanup() -> None:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)

    request.addfinalizer(cleanup)
    yield file_path


class TestRuffTool:
    """Test cases for RuffTool."""

    def test_tool_initialization(self, ruff_tool) -> None:
        """Test that RuffTool initializes correctly.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert_that(ruff_tool.name).is_equal_to("ruff")
        assert_that(ruff_tool.can_fix is True).is_true()
        assert_that(ruff_tool.config.file_patterns).contains("*.py")
        assert_that(ruff_tool.config.file_patterns).contains("*.pyi")

    def test_tool_priority(self, ruff_tool) -> None:
        """Test that RuffTool has high priority.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        assert_that(ruff_tool.config.priority).is_equal_to(85)

    def test_lint_check_clean_file(self, ruff_tool, ruff_clean_file) -> None:
        """Test Ruff lint check on a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_clean_file: Path to the static clean Python file.
        """
        ruff_tool.set_options(select=["E", "F"], format=False)
        result = ruff_tool.check([ruff_clean_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.success is True).is_true()
        assert_that(result.issues_count).is_equal_to(0)

    def test_lint_check_violations(self, ruff_tool, ruff_violation_file) -> None:
        """Test Ruff lint check on a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        ruff_tool.set_options(select=["E", "F"])
        result = ruff_tool.check([ruff_violation_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.success is False).is_true()
        assert_that(result.issues_count > 0).is_true()

    def test_check_nonexistent_file(self, ruff_tool) -> None:
        """Test checking a nonexistent file.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(FileNotFoundError):
            ruff_tool.check(["/nonexistent/file.py"])

    def test_check_empty_paths(self, ruff_tool) -> None:
        """Test checking with empty paths.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        result = ruff_tool.check([])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success is True).is_true()
        assert_that(result.output).is_equal_to("No files to check.")
        assert_that(result.issues_count).is_equal_to(0)

    def test_fix_with_violations(self, ruff_tool, temp_python_file) -> None:
        """Test fixing a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            temp_python_file: Temporary Python file with violations.
        """
        result = ruff_tool.fix([temp_python_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.output).is_not_equal_to("No fixes applied.")

    def test_set_options_valid(self, ruff_tool) -> None:
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
        assert_that(ruff_tool.options["select"]).is_equal_to(["E", "F"])
        assert_that(ruff_tool.options["ignore"]).is_equal_to(["E501"])
        assert_that(ruff_tool.options["line_length"]).is_equal_to(88)
        assert_that(ruff_tool.options["target_version"]).is_equal_to("py39")
        assert_that(ruff_tool.options["unsafe_fixes"] is True).is_true()
        assert_that(ruff_tool.options["format"] is False).is_true()

    def test_set_options_invalid_select(self, ruff_tool) -> None:
        """Test setting invalid select option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="select must be a string or list"):
            ruff_tool.set_options(select=123)

    def test_set_options_invalid_line_length(self, ruff_tool) -> None:
        """Test setting invalid line length.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        with pytest.raises(ValueError, match="line_length must be an integer"):
            ruff_tool.set_options(line_length="88")
        with pytest.raises(ValueError, match="line_length must be positive"):
            ruff_tool.set_options(line_length=-1)

    def test_build_check_command_basic(self, ruff_tool) -> None:
        """Test building basic check command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        # Ruff is run via python -m ruff, so cmd[0] is python exe, cmd[1] is "-m", cmd[2] is "ruff"
        assert_that(cmd).contains("ruff")
        assert_that(cmd).contains("check")
        assert_that(cmd).contains("--output-format")
        assert_that(cmd).contains("json")
        assert_that(cmd).contains("test.py")

    def test_build_check_command_with_fix(self, ruff_tool) -> None:
        """Test building check command with fix option.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files, fix=True)
        assert_that(cmd).contains("--fix")

    def test_build_check_command_with_options(self, ruff_tool) -> None:
        """Test building check command with various options.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["E", "F"], ignore=["E501"], line_length=88)
        files = ["test.py"]
        cmd = ruff_tool._build_check_command(files)
        assert_that(cmd).contains("--select")
        assert_that(cmd).contains("E,F")
        assert_that(cmd).contains("--ignore")
        assert_that(cmd).contains("E501")
        assert_that(cmd).contains("--line-length")
        assert_that(cmd).contains("88")

    def test_build_format_command_basic(self, ruff_tool) -> None:
        """Test building basic format command.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files)
        # Ruff is run via python -m ruff, so cmd[0] is python exe, cmd[1] is "-m", cmd[2] is "ruff"
        assert_that(cmd).contains("ruff")
        assert_that(cmd).contains("format")
        assert_that(cmd).contains("test.py")

    def test_build_format_command_check_only(self, ruff_tool) -> None:
        """Test building format command in check-only mode.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        files = ["test.py"]
        cmd = ruff_tool._build_format_command(files, check_only=True)
        assert_that(cmd).contains("--check")

    def test_check_reports_formatting_issues(self, ruff_tool, request) -> None:
        """Test that check reports formatting issues (not just lint issues).

        Args:
            ruff_tool: RuffTool fixture instance.
            request: Pytest request fixture for cleanup.
        """
        content = "def foo():\n    return 42    \n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        def cleanup() -> None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(file_path)

        request.addfinalizer(cleanup)
        ruff_tool.set_options(select=["E", "F"])
        import subprocess

        format_cmd = ["ruff", "format", "--check", file_path]
        proc = subprocess.run(format_cmd, capture_output=True, text=True)
        print("[DEBUG] ruff format --check stdout:")
        print(proc.stdout)
        print("[DEBUG] ruff format --check stderr:")
        print(proc.stderr)
        result = ruff_tool.check([file_path])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.success is False).is_true()
        assert_that(result.issues_count > 0).is_true()
        assert_that(
            any(
                (
                    getattr(issue, "file", None) == file_path
                    for issue in result.issues or []
                ),
            ),
        ).is_true()

    def test_format_check_clean_file(self, ruff_tool, ruff_clean_file) -> None:
        """Test format check on a clean file.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_clean_file: Path to the static clean Python file.
        """
        result = ruff_tool.check([ruff_clean_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success is True).is_true()
        assert_that(result.issues_count).is_equal_to(0)

    def test_format_check_violations(self, ruff_tool, ruff_violation_file) -> None:
        """Test format check on a file with violations.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        result = ruff_tool.check([ruff_violation_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success is False).is_true()
        assert_that(result.issues_count > 0).is_true()
        assert_that(result.issues and len(result.issues) > 0).is_true()

    def test_fmt_fixes_violations(self, ruff_tool, ruff_violation_file) -> None:
        """Apply fix to a file and expect fewer or equal issues after.

        Args:
            ruff_tool: RuffTool fixture instance.
            ruff_violation_file: Path to a temp file with known violations.
        """
        initial_check = ruff_tool.check([ruff_violation_file])
        initial_issues = initial_check.issues_count
        fix_result = ruff_tool.fix([ruff_violation_file])
        assert_that(isinstance(fix_result, ToolResult)).is_true()
        check_result = ruff_tool.check([ruff_violation_file])
        assert_that(isinstance(check_result, ToolResult)).is_true()
        assert check_result.issues_count <= initial_issues, (
            "Expected fewer or equal issues after fixing, but got "
            f"{check_result.issues_count} (was {initial_issues})"
        )

    def test_ruff_output_consistency_direct_vs_lintro(
        self,
        ruff_violation_file,
    ) -> None:
        """Ruff CLI vs Lintro: Should produce consistent results for the same file.

        Args:
            ruff_violation_file: Path to a temp file with known violations.
        """
        import subprocess
        from pathlib import Path

        logger.info("[TEST] Comparing ruff CLI and Lintro RuffTool outputs...")
        tool = RuffTool()
        tool.set_options()
        file_path = Path(ruff_violation_file)
        cmd = ["ruff", "check", "--isolated", "--output-format", "json", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        import json

        direct_issues = 0
        if result.stdout:
            try:
                json_end = result.stdout.rfind("]")
                if json_end != -1:
                    json_part = result.stdout[: json_end + 1]
                    data = json.loads(json_part)
                    direct_issues = len(data)
            except (json.JSONDecodeError, KeyError):
                direct_issues = len(
                    [
                        line
                        for line in result.stdout.splitlines()
                        if ":" in line
                        and any(code in line for code in ["E", "F", "I", "W"])
                    ],
                )
        lintro_result = tool.check([ruff_violation_file])
        lintro_lint_issues = (
            len(
                [
                    issue
                    for issue in lintro_result.issues
                    if hasattr(issue, "code") and issue.code != "FORMAT"
                ],
            )
            if lintro_result.issues
            else 0
        )
        logger.info(
            f"[LOG] CLI issues: {direct_issues}, "
            f"Lintro lint issues: {lintro_lint_issues}",
        )
        assert direct_issues == lintro_lint_issues, (
            "Issue count mismatch: "
            f"CLI={direct_issues}, "
            f"Lintro lint issues={lintro_lint_issues}\n"
            f"CLI Output:\n{result.stdout}\n"
            f"Lintro Output:\n{lintro_result.output}"
        )

    def test_c4_comprehensions_rules(self, ruff_tool) -> None:
        """Test C4 (flake8-comprehensions) rule detection.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["C4"])
        result = ruff_tool.check(["test_samples/ruff_c4_comprehensions_violations.py"])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.success is False).is_true()
        assert_that(result.issues_count > 0).is_true()

        # Check that C4 rules are detected
        c4_issues = [
            issue
            for issue in result.issues
            if hasattr(issue, "code") and issue.code.startswith("C4")
        ]
        assert_that(len(c4_issues)).is_greater_than(0)

    def test_sim_simplify_rules(self, ruff_tool) -> None:
        """Test SIM (flake8-simplify) rule detection.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        ruff_tool.set_options(select=["SIM"])
        result = ruff_tool.check(["test_samples/ruff_sim_simplify_violations.py"])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("ruff")
        assert_that(result.success is False).is_true()
        assert_that(result.issues_count > 0).is_true()

        # Check that SIM rules are detected
        sim_issues = [
            issue
            for issue in result.issues
            if hasattr(issue, "code") and issue.code.startswith("SIM")
        ]
        assert_that(len(sim_issues)).is_greater_than(0)

    def test_c4_comprehensions_fixing(self, ruff_tool) -> None:
        """Test C4 (flake8-comprehensions) rule fixing.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        import os
        import tempfile

        # Create a temporary file with C4 violations
        content = """
def test_function():
    numbers = [1, 2, 3, 4, 5]
    # C401: Unnecessary list comprehension
    result = [x for x in numbers]
    return result
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_file = f.name

        try:
            # Check initial issues
            ruff_tool.set_options(select=["C4"], unsafe_fixes=True)
            initial_result = ruff_tool.check([temp_file])
            initial_count = initial_result.issues_count

            # Apply fixes
            fix_result = ruff_tool.fix([temp_file])
            assert_that(fix_result.success).is_true()

            # Check remaining issues
            final_result = ruff_tool.check([temp_file])
            final_count = final_result.issues_count

            # Should have fewer issues after fixing
            assert_that(final_count).is_less_than_or_equal_to(initial_count)

        finally:
            os.unlink(temp_file)

    def test_sim_simplify_fixing(self, ruff_tool) -> None:
        """Test SIM (flake8-simplify) rule fixing.

        Args:
            ruff_tool: RuffTool fixture instance.
        """
        import os
        import tempfile

        # Create a temporary file with SIM violations
        content = """
def test_function():
    x = 5
    # SIM101: Unnecessary if-else
    if x > 0:
        result = True
    else:
        result = False
    return result
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_file = f.name

        try:
            # Check initial issues
            ruff_tool.set_options(select=["SIM"], unsafe_fixes=True)
            initial_result = ruff_tool.check([temp_file])
            initial_count = initial_result.issues_count

            # Apply fixes
            fix_result = ruff_tool.fix([temp_file])
            assert_that(fix_result.success).is_true()

            # Check remaining issues
            final_result = ruff_tool.check([temp_file])
            final_count = final_result.issues_count

            # Should have fewer issues after fixing
            assert_that(final_count).is_less_than_or_equal_to(initial_count)

        finally:
            os.unlink(temp_file)
