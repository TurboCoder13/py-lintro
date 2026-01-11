"""Execution utilities for tool execution.

This package provides utilities for tool execution including exit codes,
tool configuration, and parallel execution.
"""

from lintro.utils.execution.exit_codes import (
    DEFAULT_EXIT_CODE_FAILURE,
    DEFAULT_EXIT_CODE_SUCCESS,
    DEFAULT_REMAINING_COUNT,
    aggregate_tool_results,
    determine_exit_code,
)
from lintro.utils.execution.parallel_executor import run_tools_parallel
from lintro.utils.execution.tool_configuration import (
    configure_tool_for_execution,
    get_tool_display_name,
    get_tool_lookup_keys,
    get_tools_to_run,
)

__all__ = [
    "DEFAULT_EXIT_CODE_FAILURE",
    "DEFAULT_EXIT_CODE_SUCCESS",
    "DEFAULT_REMAINING_COUNT",
    "aggregate_tool_results",
    "configure_tool_for_execution",
    "determine_exit_code",
    "get_tool_display_name",
    "get_tool_lookup_keys",
    "get_tools_to_run",
    "run_tools_parallel",
]
