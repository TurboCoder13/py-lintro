"""Pytest test runner integration."""

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from lintro.enums.pytest_enums import PytestSpecialMode
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.tools.core.tool_base import BaseTool
from lintro.tools.implementations.pytest.pytest_command_builder import (
    build_check_command,
)
from lintro.tools.implementations.pytest.pytest_config import PytestConfiguration
from lintro.tools.implementations.pytest.pytest_error_handler import PytestErrorHandler
from lintro.tools.implementations.pytest.pytest_executor import PytestExecutor
from lintro.tools.implementations.pytest.pytest_handlers import (
    handle_check_plugins,
    handle_collect_only,
    handle_fixture_info,
    handle_list_fixtures,
    handle_list_markers,
    handle_list_plugins,
    handle_parametrize_help,
)
from lintro.tools.implementations.pytest.pytest_output_processor import (
    parse_pytest_output_with_fallback,
)
from lintro.tools.implementations.pytest.pytest_result_processor import (
    PytestResultProcessor,
)
from lintro.tools.implementations.pytest.pytest_utils import (
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
        pytest_config: PytestConfiguration: Pytest-specific configuration.
        executor: PytestExecutor: Test execution handler.
        result_processor: PytestResultProcessor: Result processing handler.
        error_handler: PytestErrorHandler: Error handling handler.
    """

    name: str = field(default="pytest")
    description: str = field(
        default="Mature full-featured Python testing tool",
    )
    can_fix: bool = field(default=False)  # pytest doesn't fix code, it runs tests
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=PYTEST_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=PYTEST_FILE_PATTERNS,
            tool_type=ToolType.TEST_RUNNER,
        ),
    )
    exclude_patterns: list[str] = field(default_factory=load_lintro_ignore)
    include_venv: bool = field(default=False)
    _default_timeout: int = PYTEST_DEFAULT_TIMEOUT

    # New component attributes
    pytest_config: PytestConfiguration = field(default_factory=PytestConfiguration)
    executor: PytestExecutor = field(init=False)
    result_processor: PytestResultProcessor = field(init=False)
    error_handler: PytestErrorHandler = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the tool after dataclass creation."""
        super().__post_init__()
        initialize_pytest_tool_config(self)

        # Initialize the new components with tool reference
        self.executor = PytestExecutor(
            config=self.pytest_config,
            tool=self,
        )
        self.result_processor = PytestResultProcessor(self.pytest_config, self.name)
        self.error_handler = PytestErrorHandler(self.name)

    def set_options(self, **kwargs: Any) -> None:
        """Set pytest-specific options.

        Args:
            **kwargs: Option key-value pairs to set.

        Delegates to PytestConfiguration for option management and validation.
        Forwards unrecognized options (like timeout) to the base class.
        """
        # Extract pytest-specific options
        config_fields = {
            field.name for field in self.pytest_config.__dataclass_fields__.values()
        }
        pytest_options = {k: v for k, v in kwargs.items() if k in config_fields}
        base_options = {k: v for k, v in kwargs.items() if k not in config_fields}

        # Set pytest-specific options
        self.pytest_config.set_options(**pytest_options)

        # Forward unrecognized options (like timeout) to base class
        if base_options:
            super().set_options(**base_options)

        # Set pytest options on the parent class (for backward compatibility)
        options_dict = self.pytest_config.get_options_dict()
        super().set_options(**options_dict)

    def _build_check_command(
        self,
        files: list[str],
        fix: bool = False,
    ) -> list[str]:
        """Build the pytest command.

        Backward compatibility method that delegates to build_check_command.

        Args:
            files: list[str]: List of files to test.
            fix: bool: Ignored for pytest (not applicable).

        Returns:
            list[str]: List of command arguments.
        """
        cmd, _ = build_check_command(self, files, fix)
        return cmd

    def _parse_output(
        self,
        output: str,
        return_code: int,
        junitxml_path: str | None = None,
        subprocess_start_time: float | None = None,
    ) -> list[Any]:
        """Parse pytest output into issues.

        Backward compatibility method that delegates to
        parse_pytest_output_with_fallback.

        Args:
            output: Raw output from pytest.
            return_code: Return code from pytest.
            junitxml_path: Optional path to JUnit XML file (from auto_junitxml).
            subprocess_start_time: Optional Unix timestamp when subprocess started.

        Returns:
            list: Parsed test failures and errors.
        """
        # Build options dict for parser
        # Use self.options but override junitxml if auto-enabled path provided
        options = self.options.copy() if junitxml_path else self.options
        if junitxml_path:
            options["junitxml"] = junitxml_path

        return parse_pytest_output_with_fallback(
            output=output,
            return_code=return_code,
            options=options,
            subprocess_start_time=subprocess_start_time,
        )

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
        special_mode = self.pytest_config.get_special_mode()
        if special_mode:
            mode_value = self.pytest_config.get_special_mode_value(special_mode)

            if special_mode == PytestSpecialMode.LIST_PLUGINS:
                return handle_list_plugins(self)
            elif special_mode == PytestSpecialMode.CHECK_PLUGINS:
                return handle_check_plugins(self, mode_value)
            elif special_mode == PytestSpecialMode.COLLECT_ONLY:
                return handle_collect_only(self, target_files)
            elif special_mode == PytestSpecialMode.LIST_FIXTURES:
                return handle_list_fixtures(self, target_files)
            elif special_mode == PytestSpecialMode.FIXTURE_INFO:
                return handle_fixture_info(self, mode_value, target_files)
            elif special_mode == PytestSpecialMode.LIST_MARKERS:
                return handle_list_markers(self)
            elif special_mode == PytestSpecialMode.PARAMETRIZE_HELP:
                return handle_parametrize_help(self)

        return None

    def check(  # type: ignore[override]
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
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result
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
        cmd, auto_junitxml_path = build_check_command(self, target_files, fix)

        logger.debug(f"Running pytest with command: {' '.join(cmd)}")
        logger.debug(f"Target files: {target_files}")

        # Prepare test execution using executor
        total_available_tests, docker_test_count, original_docker_env = (
            self.executor.prepare_test_execution(target_files)
        )
        run_docker_tests = self.pytest_config.run_docker_tests or False

        try:
            # Record start time to filter out stale junitxml files
            import time

            subprocess_start_time = time.time()

            # Execute tests using executor
            success, output, return_code = self.executor.execute_tests(cmd)

            # Parse output using _parse_output method
            # Pass auto_junitxml_path so parser knows where to find report.xml
            # Pass subprocess_start_time to filter out stale junitxml files
            issues = self._parse_output(
                output,
                return_code,
                auto_junitxml_path,
                subprocess_start_time,
            )

            # Process results using result processor
            summary_data, all_issues = self.result_processor.process_test_results(
                output=output,
                return_code=return_code,
                issues=issues,
                total_available_tests=total_available_tests,
                docker_test_count=docker_test_count,
                run_docker_tests=run_docker_tests,
            )

            # Build result using result processor
            return self.result_processor.build_result(success, summary_data, all_issues)

        except subprocess.TimeoutExpired:
            timeout_opt = self.options.get("timeout", self._default_timeout)
            if isinstance(timeout_opt, int):
                timeout_val = timeout_opt
            elif timeout_opt is not None:
                timeout_val = int(str(timeout_opt))
            else:
                timeout_val = self._default_timeout
            return self.error_handler.handle_timeout_error(
                timeout_val,
                cmd,
                initial_count=0,
            )
        except Exception as e:
            return self.error_handler.handle_execution_error(e, cmd)
        finally:
            # Restore original environment state
            self.executor.restore_environment(original_docker_env)

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
            "pytest does not support fixing issues - it only runs tests",
        )
