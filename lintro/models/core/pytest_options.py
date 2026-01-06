"""Pytest-specific configuration options."""

from dataclasses import dataclass, field

from .base_tool_options import BaseToolOptions


@dataclass
class PytestOptions(BaseToolOptions):
    """Pytest-specific configuration options.

    Attributes:
        verbose: Verbose output
        quiet: Quiet output
        tb: Traceback format
        maxfail: Stop after N failures
        strict: Strict mode
        disable_warnings: Disable warnings
        markers: Show markers
        fixtures: Show fixtures
        collect_only: Only collect tests
        list_fixtures: List fixtures
        list_markers: List markers
        parametrize_help: Show parametrize help
        fixture_info: Get fixture info
        check_plugins: Check plugin compatibility
        required_plugins: List of required plugins
        coverage_html: HTML coverage report path
        coverage_xml: XML coverage report path
        coverage_term_missing: Show missing coverage in terminal
    """

    verbose: bool | None = field(default=None)
    quiet: bool | None = field(default=None)
    tb: str | None = field(default=None)
    maxfail: int | None = field(default=None)
    strict: bool | None = field(default=None)
    disable_warnings: bool | None = field(default=None)
    markers: bool | None = field(default=None)
    fixtures: bool | None = field(default=None)
    collect_only: bool | None = field(default=None)
    list_fixtures: bool | None = field(default=None)
    list_markers: bool | None = field(default=None)
    parametrize_help: bool | None = field(default=None)
    fixture_info: str | None = field(default=None)
    check_plugins: bool | None = field(default=None)
    required_plugins: list[str] | None = field(default=None)
    coverage_html: str | None = field(default=None)
    coverage_xml: str | None = field(default=None)
    coverage_term_missing: bool | None = field(default=None)
