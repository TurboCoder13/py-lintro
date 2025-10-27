"""Pytest test runner integration."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.parsers.pytest.pytest_parser import (
    extract_pytest_summary,
    parse_pytest_output,
)
from lintro.tools.core.tool_base import BaseTool

# Constants for pytest configuration
PYTEST_DEFAULT_TIMEOUT: int = 300  # 5 minutes for test runs
PYTEST_DEFAULT_PRIORITY: int = 90
PYTEST_FILE_PATTERNS: list[str] = ["test_*.py", "*_test.py"]
PYTEST_OUTPUT_FORMAT: str = "text"
PYTEST_TEST_MODE_ENV: str = "LINTRO_TEST_MODE"
PYTEST_TEST_MODE_VALUE: str = "1"


def _load_pytest_config() -> dict:
    """Load pytest configuration from pyproject.toml or pytest.ini.

    Returns:
        dict: Pytest configuration dictionary.
    """
    config: dict = {}

    # Check pyproject.toml first
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            import tomllib

            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "tool" in pyproject_data and "pytest" in pyproject_data["tool"]:
                    config = pyproject_data["tool"]["pytest"]
        except Exception as e:
            logger.warning(
                f"Failed to load pytest configuration from pyproject.toml: {e}",
            )

    # Check pytest.ini
    pytest_ini_path = Path("pytest.ini")
    if pytest_ini_path.exists():
        try:
            import configparser

            parser = configparser.ConfigParser()
            parser.read(pytest_ini_path)
            if "pytest" in parser:
                config.update(dict(parser["pytest"]))
        except Exception as e:
            logger.warning(f"Failed to load pytest configuration from pytest.ini: {e}")

    return config


def _load_lintro_ignore() -> list[str]:
    """Load ignore patterns from .lintro-ignore file.

    Returns:
        list[str]: List of ignore patterns.
    """
    ignore_patterns: list[str] = []
    ignore_file = Path(".lintro-ignore")

    if ignore_file.exists():
        try:
            with open(ignore_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception as e:
            logger.warning(f"Failed to load .lintro-ignore: {e}")

    return ignore_patterns


@dataclass
class PytestTool(BaseTool):
    """Pytest test runner integration.

    Pytest is a mature full-featured Python testing tool that helps you write
    better programs. It supports various testing patterns and provides extensive
    configuration options.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "pytest"
    description: str = (
        "Mature full-featured Python testing tool that helps you write "
        "better programs"
    )
    can_fix: bool = False  # pytest doesn't fix code, it runs tests
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=PYTEST_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=PYTEST_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
        ),
    )
    exclude_patterns: list[str] = field(default_factory=_load_lintro_ignore)
    include_venv: bool = False
    _default_timeout: int = PYTEST_DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        """Initialize the tool after dataclass creation."""
        super().__post_init__()

        # Load pytest configuration
        pytest_config = _load_pytest_config()

        # Set default options based on configuration
        default_options = {
            "verbose": True,
            "tb": "short",  # Traceback format
            "maxfail": None,  # Don't stop early - run all tests
            "no_header": True,
            "disable_warnings": True,
        }

        # Override with config file settings
        if pytest_config and "addopts" in pytest_config:
            # Parse addopts string
            addopts = pytest_config["addopts"].split()
            for opt in addopts:
                if opt.startswith("--"):
                    key = opt[2:].replace("-", "_")
                    default_options[key] = True
                elif opt.startswith("-"):
                    key = opt[1:].replace("-", "_")
                    default_options[key] = True

        self.options.update(default_options)

    def set_options(
        self,
        verbose: bool | None = None,
        tb: str | None = None,
        maxfail: int | None = None,
        no_header: bool | None = None,
        disable_warnings: bool | None = None,
        json_report: bool | None = None,
        junitxml: str | None = None,
        run_docker_tests: bool | None = None,
        **kwargs,
    ) -> None:
        """Set pytest-specific options.

        Args:
            verbose: Enable verbose output.
            tb: Traceback format (short, long, auto, line, native).
            maxfail: Stop after first N failures.
            no_header: Disable header.
            disable_warnings: Disable warnings.
            json_report: Enable JSON report output.
            junitxml: Path for JUnit XML output.
            run_docker_tests: Enable Docker tests (default: False).
            **kwargs: Additional options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if verbose is not None and not isinstance(verbose, bool):
            raise ValueError("verbose must be a boolean")

        if tb is not None and tb not in ("short", "long", "auto", "line", "native"):
            raise ValueError("tb must be one of: short, long, auto, line, native")

        if maxfail is not None and not isinstance(maxfail, int):
            raise ValueError("maxfail must be an integer")

        if no_header is not None and not isinstance(no_header, bool):
            raise ValueError("no_header must be a boolean")

        if disable_warnings is not None and not isinstance(disable_warnings, bool):
            raise ValueError("disable_warnings must be a boolean")

        if json_report is not None and not isinstance(json_report, bool):
            raise ValueError("json_report must be a boolean")

        if junitxml is not None and not isinstance(junitxml, str):
            raise ValueError("junitxml must be a string")

        if run_docker_tests is not None and not isinstance(run_docker_tests, bool):
            raise ValueError("run_docker_tests must be a boolean")

        options: dict = {
            "verbose": verbose,
            "tb": tb,
            "maxfail": maxfail,
            "no_header": no_header,
            "disable_warnings": disable_warnings,
            "json_report": json_report,
            "junitxml": junitxml,
            "run_docker_tests": run_docker_tests,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_check_command(
        self,
        files: list[str],
        fix: bool = False,
    ) -> list[str]:
        """Build the pytest command.

        Args:
            files: list[str]: List of files to test.
            fix: bool: Ignored for pytest (not applicable).

        Returns:
            list[str]: List of command arguments.
        """
        cmd: list[str] = self._get_executable_command(tool_name="pytest")

        # Add verbosity
        if self.options.get("verbose", True):
            cmd.append("-v")

        # Add traceback format
        tb_format = self.options.get("tb", "short")
        cmd.extend(["--tb", tb_format])

        # Add maxfail only if specified
        # Note: We default to None to avoid stopping early and run all tests
        maxfail = self.options.get("maxfail")
        if maxfail is not None:
            cmd.extend(["--maxfail", str(maxfail)])
        else:
            # Explicitly set maxfail=0 to run all tests when not specified
            # This overrides pytest.ini addopts which may have --maxfail=3
            cmd.extend(["--maxfail", "0"])

        # Add no-header
        if self.options.get("no_header", True):
            cmd.append("--no-header")

        # Add disable-warnings
        if self.options.get("disable_warnings", True):
            cmd.append("--disable-warnings")

        # Add output format options
        if self.options.get("json_report", False):
            cmd.append("--json-report")
            cmd.append("--json-report-file=pytest-report.json")

        if self.options.get("junitxml"):
            cmd.extend(["--junitxml", self.options["junitxml"]])

        # Add test mode isolation if in test mode
        if os.environ.get(PYTEST_TEST_MODE_ENV) == PYTEST_TEST_MODE_VALUE:
            cmd.append("--strict-markers")
            cmd.append("--strict-config")

        # Add files
        cmd.extend(files)

        return cmd

    def _parse_output(
        self,
        output: str,
        return_code: int,
    ) -> list[PytestIssue]:
        """Parse pytest output into issues.

        Args:
            output: Raw output from pytest.
            return_code: Return code from pytest.

        Returns:
            list[PytestIssue]: Parsed test failures and errors.
        """
        # Determine output format
        output_format = "text"
        if self.options.get("json_report", False):
            output_format = "json"
        elif self.options.get("junitxml"):
            output_format = "junit"

        # Parse based on format
        issues = parse_pytest_output(output, format=output_format)

        # If no issues found but return code indicates failure, try text parsing
        if not issues and return_code != 0:
            issues = parse_pytest_output(output, format="text")

        return issues

    def _get_total_test_count(self, target_files: list[str]) -> int:
        """Get total count of all available tests (including deselected ones).

        Args:
            target_files: list[str]: Files or directories to check.

        Returns:
            int: Total number of tests that exist.
        """
        try:
            # Use pytest --collect-only to list all tests
            collect_cmd = self._get_executable_command(tool_name="pytest")
            collect_cmd.extend(["--collect-only", "-q"])
            collect_cmd.extend(target_files)

            # Temporarily enable all tests to see total count
            original_docker_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"

            try:
                success, output = self._run_subprocess(collect_cmd)
                if not success:
                    return 0

                # Extract the total count from collection output
                # Format: "XXXX tests collected in Y.YYs"
                match = re.search(r"(\d+)\s+tests\s+collected", output)
                if match:
                    return int(match.group(1))

                return 0
            finally:
                # Restore original environment
                if original_docker_env is not None:
                    os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_docker_env
                elif "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                    del os.environ["LINTRO_RUN_DOCKER_TESTS"]
        except Exception as e:
            logger.debug(f"Failed to get total test count: {e}")
            return 0

    def _count_docker_tests(self, target_files: list[str]) -> int:
        """Count docker tests that would be skipped.

        Args:
            target_files: list[str]: Files or directories to check.

        Returns:
            int: Number of docker tests found.
        """
        try:
            # Use pytest --collect-only to list all tests
            collect_cmd = self._get_executable_command(tool_name="pytest")
            collect_cmd.extend(["--collect-only", "-q"])
            collect_cmd.extend(target_files)

            # Temporarily disable docker tests to see what would be skipped
            original_docker_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]

            try:
                success, output = self._run_subprocess(collect_cmd)
                if not success:
                    return 0

                # Count test functions under tests/scripts/docker/
                # Track when we're inside the docker directory and count Function items
                docker_test_count = 0
                in_docker_dir = False
                depth = 0

                for line in output.splitlines():
                    # Stop counting when we hit coverage section
                    if "coverage:" in line or "TOTAL" in line:
                        break

                    stripped = line.strip()

                    # Check if we're entering the docker directory
                    if "<Dir docker>" in line or "<Package docker>" in line:
                        in_docker_dir = True
                        depth = len(line) - len(stripped)  # Track indentation level
                        continue

                    # Check if we're leaving the docker directory
                    # (next directory at same or higher level)
                    if in_docker_dir and stripped.startswith("<"):
                        current_depth = len(line) - len(stripped)
                        if current_depth <= depth and not stripped.startswith(
                            "<Function",
                        ):
                            # We've left the docker directory
                            # (backed up to same or higher level)
                            in_docker_dir = False
                            continue

                    # Count Function items while inside docker directory
                    if in_docker_dir and "<Function" in line:
                        docker_test_count += 1

                return docker_test_count
            finally:
                # Restore original environment
                if original_docker_env is not None:
                    os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_docker_env
        except Exception as e:
            logger.debug(f"Failed to count docker tests: {e}")
            return 0

    def check(
        self,
        files: list[str] | None = None,
        paths: list[str] | None = None,
        fix: bool = False,
    ) -> ToolResult:
        """Run pytest on specified files.

        Args:
            files: list[str] | None: Files to test. If None, uses file patterns.
            paths: list[str] | None: Paths to test. If None, uses "tests" directory.
            fix: bool: Ignored for pytest.

        Returns:
            ToolResult: Results from pytest execution.
        """
        # For pytest, when no specific files are provided, use directories to let
        # pytest discover all tests. This allows running all tests by default.
        target_files = paths or files
        if target_files is None:
            # Default to "tests" directory to match pytest conventions
            target_files = ["tests"]
        elif (
            isinstance(target_files, list)
            and len(target_files) == 1
            and target_files[0] == "."
        ):
            # If just "." is provided, also default to "tests" directory
            target_files = ["tests"]

        cmd = self._build_check_command(target_files, fix)

        logger.debug(f"Running pytest with command: {' '.join(cmd)}")
        logger.debug(f"Target files: {target_files}")

        # Docker tests are disabled by default and must be explicitly enabled
        run_docker_tests = self.options.get("run_docker_tests", False)

        # Get total count of all tests (including deselected ones)
        total_available_tests = self._get_total_test_count(target_files)

        # Count docker tests before execution
        docker_test_count = self._count_docker_tests(target_files)

        if run_docker_tests:
            # Set environment variable to enable Docker tests
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"
            # Log that Docker tests are enabled (may take longer) in blue format
            docker_msg = (
                f"[LINTRO] Docker tests enabled ({docker_test_count} tests) - "
                "this may take longer than usual."
            )
            logger.info(f"\033[36;1m{docker_msg}\033[0m")
        elif docker_test_count > 0:
            # Log that Docker tests are disabled in blue format
            docker_msg = (
                f"[LINTRO] Docker tests disabled "
                f"({docker_test_count} tests not collected). "
                "Use --enable-docker to include them."
            )
            logger.info(f"\033[36;1m{docker_msg}\033[0m")

        try:
            success, output = self._run_subprocess(cmd)
            # Parse output with actual success status
            # (pytest returns non-zero on failures)
            return_code = 0 if success else 1
            issues = self._parse_output(output, return_code)

            # Extract summary statistics
            summary = extract_pytest_summary(output)

            # Filter to only failed/error issues for display
            failed_issues = [
                issue for issue in issues if issue.test_status in ("FAILED", "ERROR")
            ]

            # Use actual failed issues count, not summary count
            # (in case parsing is inconsistent)
            actual_failures = len(failed_issues)

            # Store summary data in output metadata with actual failures count
            import json

            # Calculate docker skipped tests
            # If docker tests are disabled and we have some,
            # they're in the skipped count
            docker_skipped = 0
            if not run_docker_tests and docker_test_count > 0:
                # The skipped count should include docker tests
                docker_skipped = min(docker_test_count, summary.skipped)

            # Calculate actual skipped tests (tests that exist but weren't run)
            # This includes deselected tests that pytest doesn't report in summary
            collected_tests = (
                summary.passed + actual_failures + summary.skipped + summary.error
            )
            actual_skipped = total_available_tests - collected_tests

            logger.debug(f"Total available tests: {total_available_tests}")
            logger.debug(f"Collected tests: {collected_tests}")
            logger.debug(
                f"Summary: passed={summary.passed}, "
                f"failed={actual_failures}, "
                f"skipped={summary.skipped}, "
                f"error={summary.error}",
            )
            logger.debug(f"Actual skipped: {actual_skipped}")

            # Use the larger of summary.skipped or actual_skipped
            # (summary.skipped is runtime skips, actual_skipped includes deselected)
            total_skipped = max(summary.skipped, actual_skipped)

            summary_data = {
                "passed": summary.passed,
                # Use actual parsed failures, not regex summary
                "failed": actual_failures,
                "skipped": total_skipped,
                "error": summary.error,
                "docker_skipped": docker_skipped,
                "duration": summary.duration,
                "total": total_available_tests,
            }

            # Build output with summary and failure details
            output_lines = [json.dumps(summary_data)]

            # If there are failures, format them as a table
            if failed_issues:
                # Import the pytest formatter to format failures as a table
                from lintro.formatters.tools.pytest_formatter import (
                    format_pytest_issues,
                )

                # Format failures as a table (will be empty if no failures)
                failures_table = format_pytest_issues(failed_issues, format="grid")
                if failures_table.strip():
                    output_lines.append("")  # Blank line before failures
                    output_lines.append("Test Failures:")
                    output_lines.append(failures_table)

            result = ToolResult(
                name=self.name,
                success=success,
                issues=failed_issues,
                output="\n".join(output_lines),
                issues_count=actual_failures,  # Count actual parsed failures
            )

            # Store summary data for display in Execution Summary table
            result.pytest_summary = summary_data

            return result
        except Exception as e:
            logger.error(f"Error running pytest: {e}")
            return ToolResult(
                name=self.name,
                success=False,
                issues=[],
                output=f"Error: {e}",
            )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files.

        Args:
            paths: list[str]: List of file paths to fix.

        Raises:
            NotImplementedError: pytest does not support fixing issues.
        """
        if not self.can_fix:
            raise NotImplementedError(f"{self.name} does not support fixing issues")

        # pytest doesn't fix code, it runs tests
        raise NotImplementedError(
            "pytest does not support fixing issues - " "it only runs tests",
        )
