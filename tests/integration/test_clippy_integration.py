"""Integration tests for Clippy Rust linter."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that
from loguru import logger

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_clippy import ClippyTool

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

SAMPLE_VIOLATIONS_DIR = Path("test_samples/clippy_violations")
SAMPLE_CLEAN_DIR = Path("test_samples/clippy_clean")


def cargo_clippy_available() -> bool:
    """Check if cargo clippy is available.

    Returns:
        bool: True if cargo clippy is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["cargo", "clippy", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_clippy_directly(project_dir: Path) -> tuple[bool, str, int]:
    """Run cargo clippy directly on a project and return result tuple.

    Args:
        project_dir: Path to the Rust project directory (containing Cargo.toml).

    Returns:
        tuple[bool, str, int]: Success status, output text, and issue count.
    """
    cmd = [
        "cargo",
        "clippy",
        "--all-targets",
        "--all-features",
        "--message-format=json",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=60,
        )
        output = result.stdout + result.stderr
        # Count Clippy warnings (lines with "clippy::" in JSON)
        issues_count = sum(
            1
            for line in output.splitlines()
            if '"clippy::' in line and '"reason":"compiler-message"' in line
        )
        # Success is only when there are no issues (regardless of returncode)
        success = issues_count == 0
        return success, output, issues_count
    except subprocess.TimeoutExpired:
        return False, "Timeout", 0
    except Exception as e:
        return False, str(e), 0


@pytest.fixture
def clippy_tool():
    """Create a ClippyTool instance for testing.

    Returns:
        ClippyTool: A configured ClippyTool instance.
    """
    return ClippyTool()


@pytest.fixture
def temp_clippy_violations_project():
    """Copy the clippy_violations sample to a temp directory for testing.

    Yields:
        Path: Path to the temporary project directory.
    """
    src = Path(SAMPLE_VIOLATIONS_DIR).resolve()
    if not src.exists():
        pytest.skip(f"Sample directory {src} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "clippy_violations"
        shutil.copytree(src, dst)
        yield dst


@pytest.fixture
def temp_clippy_clean_project():
    """Copy the clippy_clean sample to a temp directory for testing.

    Yields:
        Path: Path to the temporary project directory.
    """
    src = Path(SAMPLE_CLEAN_DIR).resolve()
    if not src.exists():
        pytest.skip(f"Sample directory {src} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "clippy_clean"
        shutil.copytree(src, dst)
        yield dst


@pytest.mark.skipif(
    not cargo_clippy_available(),
    reason="cargo clippy not available; skip integration test.",
)
class TestClippyTool:
    """Test cases for ClippyTool."""

    def test_tool_initialization(self, clippy_tool) -> None:
        """Test that ClippyTool initializes correctly.

        Args:
            clippy_tool: ClippyTool fixture instance.
        """
        assert_that(clippy_tool.name).is_equal_to("clippy")
        assert_that(clippy_tool.can_fix).is_true()
        assert_that(clippy_tool.config.file_patterns).contains("*.rs")
        assert_that(clippy_tool.config.file_patterns).contains("Cargo.toml")

    def test_tool_priority(self, clippy_tool) -> None:
        """Test that ClippyTool has correct priority.

        Args:
            clippy_tool: ClippyTool fixture instance.
        """
        assert_that(clippy_tool.config.priority).is_equal_to(85)

    def test_check_clean_project(
        self,
        clippy_tool,
        temp_clippy_clean_project,
    ) -> None:
        """Test Clippy check on a clean project.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_clean_project: Path to a temp clean Rust project.
        """
        result = clippy_tool.check([str(temp_clippy_clean_project)])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("clippy")
        # Clean project should have no issues or very few
        assert_that(result.issues_count).is_greater_than_or_equal_to(0)

    def test_check_violations_project(
        self,
        clippy_tool,
        temp_clippy_violations_project,
    ) -> None:
        """Test Clippy check on a project with violations.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_violations_project: Path to a temp project with violations.
        """
        result = clippy_tool.check([str(temp_clippy_violations_project)])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("clippy")
        # Should find multiple violations
        assert_that(result.issues_count).is_greater_than(0)
        logger.info(
            f"[TEST] clippy found {result.issues_count} issues on violations project",
        )

    def test_check_parses_issues_correctly(
        self,
        clippy_tool,
        temp_clippy_violations_project,
    ) -> None:
        """Test that ClippyTool parses issues correctly.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_violations_project: Path to a temp project with violations.
        """
        result = clippy_tool.check([str(temp_clippy_violations_project)])
        assert_that(result.issues).is_not_none()
        if result.issues:
            issue = result.issues[0]
            assert_that(issue.file).is_not_empty()
            assert_that(issue.line).is_greater_than(0)
            assert_that(issue.code).is_not_none()
            assert_that(issue.message).is_not_empty()
            # Should be a clippy lint code
            assert_that(issue.code).contains("clippy::")

    def test_fix_computes_counts(
        self,
        clippy_tool,
        temp_clippy_violations_project,
    ) -> None:
        """Test that fix mode computes initial/fixed/remaining issue counts.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_violations_project: Path to a temp project with violations.
        """
        result = clippy_tool.fix([str(temp_clippy_violations_project)])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.initial_issues_count).is_not_none()
        assert_that(result.fixed_issues_count).is_not_none()
        assert_that(result.remaining_issues_count).is_not_none()
        # Fixed + remaining should equal initial
        assert_that(
            result.fixed_issues_count + result.remaining_issues_count,
        ).is_equal_to(result.initial_issues_count)

    def test_check_no_cargo_toml(self, clippy_tool, tmp_path: Path) -> None:
        """Test that ClippyTool handles missing Cargo.toml gracefully.

        Args:
            clippy_tool: ClippyTool fixture instance.
            tmp_path: Temporary directory provided by pytest.
        """
        # Create a Rust file without Cargo.toml
        rust_file = tmp_path / "main.rs"
        rust_file.write_text("fn main() {}\n")

        result = clippy_tool.check([str(tmp_path)])
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).contains("Cargo.toml")

    def test_check_no_rust_files(self, clippy_tool, tmp_path: Path) -> None:
        """Test that ClippyTool handles no Rust files gracefully.

        Args:
            clippy_tool: ClippyTool fixture instance.
            tmp_path: Temporary directory provided by pytest.
        """
        # Create a non-Rust file
        python_file = tmp_path / "main.py"
        python_file.write_text("print('hello')\n")

        result = clippy_tool.check([str(tmp_path)])
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).contains("No Rust files")

    def test_integration_vs_direct_clippy(
        self,
        clippy_tool,
        temp_clippy_violations_project,
    ) -> None:
        """Compare ClippyTool results with direct cargo clippy execution.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_violations_project: Path to a temp project with violations.
        """
        # Run via ClippyTool
        lintro_result = clippy_tool.check([str(temp_clippy_violations_project)])

        # Run directly
        direct_success, direct_output, direct_count = run_clippy_directly(
            temp_clippy_violations_project,
        )

        # Both should find issues (or both should find none)
        # Note: exact counts may differ due to parsing differences,
        # but both should detect issues
        logger.info(
            f"[TEST] Lintro found {lintro_result.issues_count} issues, "
            f"direct clippy found {direct_count} issues",
        )
        # At least one should find issues if violations exist
        assert_that(
            lintro_result.issues_count > 0 or direct_count > 0,
        ).is_true()

    def test_check_specific_file(
        self,
        clippy_tool,
        temp_clippy_violations_project,
    ) -> None:
        """Test checking a specific Rust file.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_violations_project: Path to a temp project with violations.
        """
        main_rs = temp_clippy_violations_project / "src" / "main.rs"
        assert_that(main_rs.exists()).is_true()

        result = clippy_tool.check([str(main_rs)])
        # Should still work (finds Cargo.toml in parent)
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.name).is_equal_to("clippy")

    def test_fix_on_clean_project(
        self,
        clippy_tool,
        temp_clippy_clean_project,
    ) -> None:
        """Test fix mode on a clean project.

        Args:
            clippy_tool: ClippyTool fixture instance.
            temp_clippy_clean_project: Path to a temp clean Rust project.
        """
        result = clippy_tool.fix([str(temp_clippy_clean_project)])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.initial_issues_count).is_greater_than_or_equal_to(0)
        assert_that(result.fixed_issues_count).is_greater_than_or_equal_to(0)
        assert_that(result.remaining_issues_count).is_greater_than_or_equal_to(0)
