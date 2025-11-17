"""Pytest test runner integration."""

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.tools.core.tool_base import BaseTool
from lintro.tools.implementations.pytest_command_builder import build_check_command
from lintro.tools.implementations.pytest_handlers import (
    handle_check_plugins,
    handle_collect_only,
    handle_fixture_info,
    handle_list_fixtures,
    handle_list_markers,
    handle_list_plugins,
    handle_parametrize_help,
)
from lintro.tools.implementations.pytest_option_validators import (
    validate_pytest_options,
)
from lintro.tools.implementations.pytest_output_processor import (
    build_output_with_failures,
    check_total_time_warning,
    detect_and_log_flaky_tests,
    detect_and_log_slow_tests,
    parse_pytest_output_with_fallback,
    process_test_summary,
)
from lintro.tools.implementations.pytest_utils import (
    collect_tests_once,
    initialize_pytest_tool_config,
    load_lintro_ignore,
)

# Constants for pytest configuration
PYTEST_DEFAULT_TIMEOUT: int = 300  # 5 minutes for test runs
PYTEST_DEFAULT_PRIORITY: int = 90
PYTEST_FILE_PATTERNS: list[str] = ["test_*.py", "*_test.py"]


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
            tool_type=ToolType.TEST_RUNNER,
        ),
    )
    exclude_patterns: list[str] = field(default_factory=load_lintro_ignore)
    include_venv: bool = False
    _default_timeout: int = PYTEST_DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        """Initialize the tool after dataclass creation."""
        super().__post_init__()
        initialize_pytest_tool_config(self)

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
        slow_test_threshold: float | None = None,
        total_time_warning: float | None = None,
        workers: str | None = None,
        coverage_threshold: float | None = None,
        auto_junitxml: bool | None = None,
        detect_flaky: bool | None = None,
        flaky_min_runs: int | None = None,
        flaky_failure_rate: float | None = None,
        html_report: str | None = None,
        parallel_preset: str | None = None,
        list_plugins: bool | None = None,
        check_plugins: bool | None = None,
        required_plugins: str | None = None,
        coverage_html: str | None = None,
        coverage_xml: str | None = None,
        coverage_report: bool | None = None,
        collect_only: bool | None = None,
        list_fixtures: bool | None = None,
        fixture_info: str | None = None,
        list_markers: bool | None = None,
        parametrize_help: bool | None = None,
        show_progress: bool | None = None,
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
            slow_test_threshold: Duration threshold in seconds for slow test warning
                (default: 1.0).
            total_time_warning: Total execution time threshold in seconds for warning
                (default: 60.0).
            workers: Number of parallel workers for pytest-xdist (auto, N, or None).
            coverage_threshold: Minimum coverage percentage to require (0-100).
            auto_junitxml: Auto-enable junitxml in CI environments (default: True).
            detect_flaky: Enable flaky test detection (default: True).
            flaky_min_runs: Minimum runs before detecting flaky tests (default: 3).
            flaky_failure_rate: Minimum failure rate to consider flaky (default: 0.3).
            html_report: Path for HTML report output (pytest-html plugin).
            parallel_preset: Parallel execution preset (auto, small, medium, large).
            list_plugins: List all installed pytest plugins.
            check_plugins: Check if required plugins are installed.
            required_plugins: Comma-separated list of required plugin names.
            coverage_html: Path for HTML coverage report (requires pytest-cov).
            coverage_xml: Path for XML coverage report (requires pytest-cov).
            coverage_report: Generate both HTML and XML coverage reports.
            collect_only: List tests without executing them.
            list_fixtures: List all available fixtures.
            fixture_info: Show detailed information about a specific fixture.
            list_markers: List all available markers.
            parametrize_help: Show help for parametrized tests.
            show_progress: Show progress during test execution (default: True).
            **kwargs: Additional options.
        """
        # Validate all options using extracted validator
        validate_pytest_options(
            verbose=verbose,
            tb=tb,
            maxfail=maxfail,
            no_header=no_header,
            disable_warnings=disable_warnings,
            json_report=json_report,
            junitxml=junitxml,
            run_docker_tests=run_docker_tests,
            slow_test_threshold=slow_test_threshold,
            total_time_warning=total_time_warning,
            workers=workers,
            coverage_threshold=coverage_threshold,
            auto_junitxml=auto_junitxml,
            detect_flaky=detect_flaky,
            flaky_min_runs=flaky_min_runs,
            flaky_failure_rate=flaky_failure_rate,
            html_report=html_report,
            parallel_preset=parallel_preset,
            list_plugins=list_plugins,
            check_plugins=check_plugins,
            required_plugins=required_plugins,
            coverage_html=coverage_html,
            coverage_xml=coverage_xml,
            coverage_report=coverage_report,
            collect_only=collect_only,
            list_fixtures=list_fixtures,
            fixture_info=fixture_info,
            list_markers=list_markers,
            parametrize_help=parametrize_help,
            show_progress=show_progress,
        )

        # Set default junitxml if auto_junitxml is enabled and junitxml not
        # explicitly set
        if junitxml is None and (auto_junitxml is None or auto_junitxml):
            junitxml = "report.xml"

        options: dict = {
            "verbose": verbose,
            "tb": tb,
            "maxfail": maxfail,
            "no_header": no_header,
            "disable_warnings": disable_warnings,
            "json_report": json_report,
            "junitxml": junitxml,
            "run_docker_tests": run_docker_tests,
            "slow_test_threshold": slow_test_threshold,
            "total_time_warning": total_time_warning,
            "workers": workers,
            "coverage_threshold": coverage_threshold,
            "auto_junitxml": auto_junitxml,
            "detect_flaky": detect_flaky,
            "flaky_min_runs": flaky_min_runs,
            "flaky_failure_rate": flaky_failure_rate,
            "html_report": html_report,
            "parallel_preset": parallel_preset,
            "list_plugins": list_plugins,
            "check_plugins": check_plugins,
            "required_plugins": required_plugins,
            "coverage_html": coverage_html,
            "coverage_xml": coverage_xml,
            "coverage_report": coverage_report,
            "collect_only": collect_only,
            "list_fixtures": list_fixtures,
            "fixture_info": fixture_info,
            "list_markers": list_markers,
            "parametrize_help": parametrize_help,
            "show_progress": show_progress,
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

        Wrapper method for backward compatibility with tests.
        Delegates to build_check_command from pytest_command_builder.

        Args:
            files: list[str]: List of files to test.
            fix: bool: Ignored for pytest (not applicable).

        Returns:
            list[str]: List of command arguments.
        """
        return build_check_command(self, files, fix)

    def _parse_output(
        self,
        output: str,
        return_code: int,
    ) -> list:
        """Parse pytest output into issues.

        Wrapper method for backward compatibility with tests.
        Delegates to parse_pytest_output_with_fallback from pytest_output_processor.

        Args:
            output: Raw output from pytest.
            return_code: Return code from pytest.

        Returns:
            list: Parsed test failures and errors.
        """
        return parse_pytest_output_with_fallback(
            output=output,
            return_code=return_code,
            options=self.options,
        )

    def _collect_tests_once(
        self,
        target_files: list[str],
    ) -> tuple[int, int]:
        """Collect tests once and return both total count and docker test count.

        Wrapper method for backward compatibility with tests.
        Delegates to collect_tests_once from pytest_utils.

        Args:
            target_files: Files or directories to check.

        Returns:
            tuple[int, int]: Tuple of (total_test_count, docker_test_count).
        """
        return collect_tests_once(self, target_files)

    def _get_total_test_count(self, target_files: list[str]) -> int:
        """Get total count of all available tests.

        Wrapper method for backward compatibility with tests.
        Delegates to get_total_test_count from pytest_utils.

        Args:
            target_files: Files or directories to check.

        Returns:
            int: Total number of tests that exist.
        """
        from lintro.tools.implementations.pytest_utils import get_total_test_count

        return get_total_test_count(self, target_files)

    def _count_docker_tests(self, target_files: list[str]) -> int:
        """Count docker tests that would be skipped.

        Wrapper method for backward compatibility with tests.
        Delegates to count_docker_tests from pytest_utils.

        Args:
            target_files: Files or directories to check.

        Returns:
            int: Number of docker tests found.
        """
        from lintro.tools.implementations.pytest_utils import count_docker_tests

        return count_docker_tests(self, target_files)

    def _handle_special_modes(
        self,
        target_files: list[str],
    ) -> ToolResult | None:
        """Handle special modes that don't run tests.

        Args:
            target_files: Files or directories to operate on.

        Returns:
            ToolResult | None: Result if a special mode was handled, None otherwise.
        """
        if self.options.get("list_plugins", False):
            return self._handle_list_plugins()

        if self.options.get("check_plugins", False):
            required_plugins = self.options.get("required_plugins")
            return self._handle_check_plugins(required_plugins)

        if self.options.get("collect_only", False):
            return self._handle_collect_only(target_files)

        if self.options.get("list_fixtures", False):
            return self._handle_list_fixtures(target_files)

        fixture_info = self.options.get("fixture_info")
        if fixture_info:
            return self._handle_fixture_info(fixture_info, target_files)

        if self.options.get("list_markers", False):
            return self._handle_list_markers()

        if self.options.get("parametrize_help", False):
            return self._handle_parametrize_help()

        return None

    def _handle_list_plugins(self) -> ToolResult:
        """Handle list plugins mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_list_plugins from pytest_handlers.

        Returns:
            ToolResult: Results with plugin list.
        """
        return handle_list_plugins(self)

    def _handle_check_plugins(self, required_plugins: str | None) -> ToolResult:
        """Handle check plugins mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_check_plugins from pytest_handlers.

        Args:
            required_plugins: Comma-separated list of required plugin names.

        Returns:
            ToolResult: Results with plugin check status.
        """
        return handle_check_plugins(self, required_plugins)

    def _handle_collect_only(self, target_files: list[str]) -> ToolResult:
        """Handle collect-only mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_collect_only from pytest_handlers.

        Args:
            target_files: Files or directories to collect tests from.

        Returns:
            ToolResult: Results with collected test list.
        """
        return handle_collect_only(self, target_files)

    def _handle_list_fixtures(self, target_files: list[str]) -> ToolResult:
        """Handle list fixtures mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_list_fixtures from pytest_handlers.

        Args:
            target_files: Files or directories to collect fixtures from.

        Returns:
            ToolResult: Results with fixture list.
        """
        return handle_list_fixtures(self, target_files)

    def _handle_fixture_info(
        self,
        fixture_name: str,
        target_files: list[str],
    ) -> ToolResult:
        """Handle fixture info mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_fixture_info from pytest_handlers.

        Args:
            fixture_name: Name of fixture to get info for.
            target_files: Files or directories to search.

        Returns:
            ToolResult: Results with fixture information.
        """
        return handle_fixture_info(self, fixture_name, target_files)

    def _handle_list_markers(self) -> ToolResult:
        """Handle list markers mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_list_markers from pytest_handlers.

        Returns:
            ToolResult: Results with marker list.
        """
        return handle_list_markers(self)

    def _handle_parametrize_help(self) -> ToolResult:
        """Handle parametrize help mode.

        Wrapper method for backward compatibility with tests.
        Delegates to handle_parametrize_help from pytest_handlers.

        Returns:
            ToolResult: Results with parametrization help.
        """
        return handle_parametrize_help(self)

    def _prepare_test_execution(
        self,
        target_files: list[str],
    ) -> tuple[int, int, str | None]:
        """Prepare test execution by collecting tests and setting up environment.

        Args:
            target_files: Files or directories to test.

        Returns:
            tuple[int, int, str | None]: Tuple of (total_available_tests,
                docker_test_count, original_docker_env).
        """
        # Docker tests are disabled by default and must be explicitly enabled
        run_docker_tests = self.options.get("run_docker_tests", False)

        # Store original environment state for cleanup
        original_docker_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")

        # Collect tests once and get both total count and docker test count
        # This avoids duplicate pytest --collect-only calls
        total_available_tests, docker_test_count = self._collect_tests_once(
            target_files,
        )

        if run_docker_tests:
            # Set environment variable to enable Docker tests
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"
            # Log that Docker tests are enabled (may take longer) in blue format
            docker_msg = (
                f"[LINTRO] Docker tests enabled ({docker_test_count} tests) - "
                "this may take longer than usual."
            )
            logger.info(f"\033[36;1m{docker_msg}\033[0m")
        else:
            # Explicitly unset the environment variable to disable Docker tests
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]

            if docker_test_count > 0:
                # Log that Docker tests are disabled in blue format
                docker_msg = (
                    f"[LINTRO] Docker tests disabled "
                    f"({docker_test_count} tests not collected). "
                    "Use --enable-docker to include them."
                )
                logger.info(f"\033[36;1m{docker_msg}\033[0m")

        return (total_available_tests, docker_test_count, original_docker_env)

    def _execute_tests(
        self,
        cmd: list[str],
    ) -> tuple[bool, str, int]:
        """Execute pytest tests and parse output.

        Args:
            cmd: Command to execute.

        Returns:
            tuple[bool, str, int]: Tuple of (success, output, return_code).
        """
        success, output = self._run_subprocess(cmd)
        # Parse output with actual success status
        # (pytest returns non-zero on failures)
        return_code = 0 if success else 1
        return (success, output, return_code)

    def _process_test_results(
        self,
        output: str,
        return_code: int,
        issues: list,
        total_available_tests: int,
        docker_test_count: int,
        run_docker_tests: bool,
    ) -> tuple[dict, list]:
        """Process test results and generate summary.

        Args:
            output: Raw output from pytest.
            return_code: Return code from pytest.
            issues: Parsed test issues.
            total_available_tests: Total number of available tests.
            docker_test_count: Number of docker tests.
            run_docker_tests: Whether docker tests were enabled.

        Returns:
            tuple[dict, list]: Tuple of (summary_data, all_issues).
        """
        # Process summary
        summary_data = process_test_summary(
            output=output,
            issues=issues,
            total_available_tests=total_available_tests,
            docker_test_count=docker_test_count,
            run_docker_tests=run_docker_tests,
        )

        # Filter to only failed/error issues for the ToolResult.issues field
        # but keep all issues for formatting
        [issue for issue in issues if issue.test_status in ("FAILED", "ERROR")]

        # Performance warnings
        detect_and_log_slow_tests(issues, self.options)
        check_total_time_warning(summary_data["duration"], self.options)

        # Flaky test detection
        detect_and_log_flaky_tests(issues, self.options)

        return (summary_data, issues)

    def _build_result(
        self,
        success: bool,
        summary_data: dict,
        all_issues: list,
    ) -> ToolResult:
        """Build final ToolResult from processed data.

        Args:
            success: Whether tests passed.
            summary_data: Summary data dictionary.
            all_issues: List of all test issues (failures, errors, skips).

        Returns:
            ToolResult: Final result object.
        """
        # Filter to only failed/error issues for the ToolResult.issues field
        failed_issues = [
            issue for issue in all_issues if issue.test_status in ("FAILED", "ERROR")
        ]

        output_text = build_output_with_failures(summary_data, all_issues)

        result = ToolResult(
            name=self.name,
            success=success,
            issues=failed_issues,
            output=output_text,
            issues_count=len(failed_issues),
        )

        # Store summary data for display in Execution Summary table
        result.pytest_summary = summary_data

        return result

    def _handle_timeout_error(
        self,
        timeout_val: int,
        cmd: list[str],
        initial_count: int = 0,
    ) -> ToolResult:
        """Handle timeout errors consistently.

        Args:
            timeout_val: The timeout value that was exceeded.
            cmd: Command that timed out.
            initial_count: Number of issues discovered before timeout.

        Returns:
            ToolResult: Standardized timeout error result.
        """
        # Format the command for display
        cmd_str = " ".join(cmd[:4]) if len(cmd) >= 4 else " ".join(cmd)
        if len(cmd) > 4:
            cmd_str += f" ... ({len(cmd) - 4} more args)"

        error_msg = (
            f"❌ pytest execution timed out after {timeout_val}s\n\n"
            f"Command: {cmd_str}\n\n"
            "Possible causes:\n"
            "  • Tests are taking too long to run\n"
            "  • Some tests are hanging or blocked (e.g., waiting for I/O)\n"
            "  • Test discovery is slow or stuck\n"
            "  • Resource exhaustion (memory, file descriptors)\n\n"
            "Solutions:\n"
            "  1. Increase timeout: lintro test --tool-options timeout=600\n"
            "  2. Run fewer tests: lintro test tests/unit/ (vs full test suite)\n"
            "  3. Run in parallel: lintro test --tool-options workers=auto\n"
            "  4. Skip slow tests: lintro test -m 'not slow'\n"
            "  5. Debug directly: pytest -v --tb=short <test_file>\n"
        )
        logger.error(error_msg)
        return ToolResult(
            name=self.name,
            success=False,
            issues=[],
            output=error_msg,
            issues_count=max(initial_count, 1),  # Count timeout as execution failure
        )

    def _handle_execution_error(
        self,
        error: Exception,
        cmd: list[str],
    ) -> ToolResult:
        """Handle execution errors consistently.

        Args:
            error: The exception that occurred.
            cmd: Command that failed.

        Returns:
            ToolResult: Standardized error result.
        """
        if isinstance(error, FileNotFoundError):
            error_msg = (
                f"pytest executable not found: {error}\n\n"
                "Please ensure pytest is installed:\n"
                "  - Install via pip: pip install pytest\n"
                "  - Install via uv: uv add pytest\n"
                "  - Or install as dev dependency: uv add --dev pytest\n\n"
                "After installation, verify pytest is available:\n"
                "  pytest --version"
            )
        elif isinstance(error, subprocess.CalledProcessError):
            error_msg = (
                f"pytest execution failed with return code {error.returncode}\n\n"
                "Common causes:\n"
                "  - Syntax errors in test files\n"
                "  - Missing dependencies or imports\n"
                "  - Configuration issues in pytest.ini or pyproject.toml\n"
                "  - Permission errors accessing test files\n\n"
                "Try running pytest directly to see detailed error:\n"
                f"  {' '.join(cmd[:3])} ..."
            )
        else:
            # Generic error handling with helpful context
            error_type = type(error).__name__
            error_msg = (
                f"Unexpected error running pytest: {error_type}: {error}\n\n"
                "Please report this issue if it persists. "
                "For troubleshooting:\n"
                "  - Verify pytest is installed: pytest --version\n"
                "  - Check test files for syntax errors\n"
                "  - Review pytest configuration files\n"
                "  - Run pytest directly to see full output"
            )

        logger.error(error_msg)
        return ToolResult(
            name=self.name,
            success=False,
            issues=[],
            output=error_msg,
            issues_count=1 if isinstance(error, subprocess.TimeoutExpired) else 0,
        )

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

        # Handle special modes first (these don't run tests)
        special_result = self._handle_special_modes(target_files)
        if special_result is not None:
            return special_result

        # Normal test execution
        cmd = build_check_command(self, target_files, fix)

        logger.debug(f"Running pytest with command: {' '.join(cmd)}")
        logger.debug(f"Target files: {target_files}")

        # Prepare test execution
        total_available_tests, docker_test_count, original_docker_env = (
            self._prepare_test_execution(target_files)
        )
        run_docker_tests = self.options.get("run_docker_tests", False)

        try:
            # Execute tests
            success, output, return_code = self._execute_tests(cmd)

            # Parse output
            issues = self._parse_output(output, return_code)

            # Process results
            summary_data, failed_issues = self._process_test_results(
                output=output,
                return_code=return_code,
                issues=issues,
                total_available_tests=total_available_tests,
                docker_test_count=docker_test_count,
                run_docker_tests=run_docker_tests,
            )

            # Build result
            return self._build_result(success, summary_data, failed_issues)

        except subprocess.TimeoutExpired:
            timeout_val = self.options.get("timeout", self._default_timeout)
            return self._handle_timeout_error(timeout_val, cmd, initial_count=0)
        except Exception as e:
            return self._handle_execution_error(e, cmd)
        finally:
            # Restore original environment state
            if original_docker_env is not None:
                os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_docker_env
            elif "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]

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
