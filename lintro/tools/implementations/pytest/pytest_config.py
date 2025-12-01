"""Pytest configuration management.

This module contains the PytestConfiguration dataclass that encapsulates
all pytest-specific option management and validation logic.
"""

from dataclasses import dataclass
from typing import Any

from lintro.tools.implementations.pytest.pytest_option_validators import (
    validate_pytest_options,
)


@dataclass
class PytestConfiguration:
    """Configuration class for pytest-specific options.

    This dataclass encapsulates all pytest configuration options and provides
    validation and management methods. It follows the project's preference for
    dataclasses and proper data modeling.

    Attributes:
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
    """

    verbose: bool | None = None
    tb: str | None = None
    maxfail: int | None = None
    no_header: bool | None = None
    disable_warnings: bool | None = None
    json_report: bool | None = None
    junitxml: str | None = None
    run_docker_tests: bool | None = None
    slow_test_threshold: float | None = None
    total_time_warning: float | None = None
    workers: str | None = None
    coverage_threshold: float | None = None
    auto_junitxml: bool | None = None
    detect_flaky: bool | None = None
    flaky_min_runs: int | None = None
    flaky_failure_rate: float | None = None
    html_report: str | None = None
    parallel_preset: str | None = None
    list_plugins: bool | None = None
    check_plugins: bool | None = None
    required_plugins: str | None = None
    coverage_html: str | None = None
    coverage_xml: str | None = None
    coverage_report: bool | None = None
    collect_only: bool | None = None
    list_fixtures: bool | None = None
    fixture_info: str | None = None
    list_markers: bool | None = None
    parametrize_help: bool | None = None
    show_progress: bool | None = None

    def set_options(self, **kwargs: Any) -> None:
        """Set pytest-specific options with validation.

        Args:
            **kwargs: Option key-value pairs to set.
        """
        # Extract only the options that belong to this configuration
        config_fields = {field.name for field in self.__dataclass_fields__.values()}

        # Validate all options using extracted validator
        validate_pytest_options(
            **{k: v for k, v in kwargs.items() if k in config_fields},
        )

        # Set default junitxml if auto_junitxml is enabled and junitxml not
        # explicitly set
        junitxml = kwargs.get("junitxml")
        auto_junitxml = kwargs.get("auto_junitxml")
        if junitxml is None and (auto_junitxml is None or auto_junitxml):
            junitxml = "report.xml"
            kwargs = kwargs.copy()
            kwargs["junitxml"] = junitxml

        # Update the dataclass fields
        for key, value in kwargs.items():
            if key in config_fields:
                setattr(self, key, value)

    def get_options_dict(self) -> dict[str, Any]:
        """Get a dictionary of all non-None options.

        Returns:
            Dict[str, Any]: Dictionary of option key-value pairs, excluding None values.
        """
        options = {}
        for field_name, _field_info in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if value is not None:
                options[field_name] = value
        return options

    def is_special_mode(self) -> bool:
        """Check if any special mode is enabled.

        Special modes are modes that don't run tests but perform other operations
        like listing plugins, fixtures, etc.

        Returns:
            bool: True if any special mode is enabled.
        """
        special_modes = [
            "list_plugins",
            "check_plugins",
            "collect_only",
            "list_fixtures",
            "list_markers",
            "parametrize_help",
        ]

        # Check boolean special modes
        if any(getattr(self, mode, False) for mode in special_modes):
            return True

        # Check fixture_info (string value, not boolean)
        return bool(getattr(self, "fixture_info", None))

    def get_special_mode(self) -> str | None:
        """Get the active special mode, if any.

        Returns:
            str | None: Name of the active special mode, or None if no special mode.
        """
        special_modes = [
            ("list_plugins", "list_plugins"),
            ("check_plugins", "check_plugins"),
            ("collect_only", "collect_only"),
            ("list_fixtures", "list_fixtures"),
            ("list_markers", "list_markers"),
            ("parametrize_help", "parametrize_help"),
        ]

        for attr_name, mode_name in special_modes:
            if getattr(self, attr_name, False):
                return mode_name

        # Check for fixture_info (string value, not boolean)
        if getattr(self, "fixture_info", None):
            return "fixture_info"

        return None

    def get_special_mode_value(self, mode: str) -> Any:
        """Get the value for a special mode.

        Args:
            mode: The special mode name.

        Returns:
            Any: The value associated with the special mode.
        """
        if mode == "fixture_info":
            return self.fixture_info
        elif mode == "check_plugins":
            return self.required_plugins
        else:
            return getattr(self, mode, False)
