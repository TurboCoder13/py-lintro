"""Helper functions for tool execution.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. SimpleLintroLogger - handles console display AND logging with Loguru + rich
   formatting
3. No tee, no stream redirection, no complex state management
"""

from lintro.enums.action import Action, normalize_action
from lintro.enums.tool_name import ToolName
from lintro.enums.tools_value import ToolsValue
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum

# Constants
DEFAULT_EXIT_CODE_SUCCESS: int = 0
DEFAULT_EXIT_CODE_FAILURE: int = 1

# Mapping from ToolEnum to canonical display names
_TOOL_DISPLAY_NAMES: dict[ToolEnum, str] = {
    ToolEnum.BLACK: "black",
    ToolEnum.DARGLINT: "darglint",
    ToolEnum.HADOLINT: "hadolint",
    ToolEnum.PRETTIER: "prettier",
    ToolEnum.PYTEST: "pytest",
    ToolEnum.RUFF: "ruff",
    ToolEnum.YAMLLINT: "yamllint",
    ToolEnum.ACTIONLINT: "actionlint",
    ToolEnum.BANDIT: "bandit",
}


def _get_tool_display_name(tool_enum: ToolEnum) -> str:
    """Get the canonical display name for a tool enum.

    This function provides a consistent mapping from ToolEnum to user-friendly
    display names. It first attempts to get the tool instance to use its canonical
    name, but falls back to a predefined mapping if the tool cannot be instantiated.

    Args:
        tool_enum: The ToolEnum instance.

    Returns:
        str: The canonical display name for the tool.
    """
    # Try to get the tool instance to use its canonical name
    try:
        tool = tool_manager.get_tool(tool_enum)
        return tool.name
    except Exception:
        # Fall back to predefined mapping if tool cannot be instantiated
        return _TOOL_DISPLAY_NAMES.get(tool_enum, tool_enum.name.lower())


def _get_tool_lookup_keys(tool_enum: ToolEnum, tool_name: str) -> set[str]:
    """Get all possible lookup keys for a tool in tool_option_dict.

    This includes the tool's display name and enum name (both lowercased).

    Args:
        tool_enum: The ToolEnum instance.
        tool_name: The canonical display name for the tool.

    Returns:
        set[str]: Set of lowercase keys to check in tool_option_dict.
    """
    return {tool_name.lower(), tool_enum.name.lower()}


def _get_tools_to_run(
    tools: str | ToolsValue | None,
    action: str | Action,
) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: Comma-separated tool names, ToolsValue.ALL, or None.
        action: str | Action: "check", "fmt", "test", or Action enum.

    Returns:
        list[ToolEnum]: List of ToolEnum instances to run.

    Raises:
        ValueError: If unknown tool names are provided.
    """
    # Normalize action if it's a string
    if isinstance(action, str):
        action = normalize_action(action)

    # Normalize tools to string for processing
    if isinstance(tools, ToolsValue):
        tools_str: str | None = tools.value if tools != ToolsValue.ALL else None
    else:
        tools_str = tools

    if action == Action.TEST:
        # Test action only supports pytest
        if tools_str and tools_str.lower() != "pytest":
            raise ValueError(
                (
                    "Only 'pytest' is supported for the test action; "
                    "run 'lintro test' without --tools or "
                    "use '--tools pytest'"
                ),
            )
        try:
            return [ToolEnum["PYTEST"]]
        except KeyError:
            raise ValueError(
                "pytest tool is not available",
            ) from None

    if tools_str is None or (isinstance(tools_str, str) and tools_str.lower() == "all"):
        # Get all available tools for the action
        if action == Action.FIX:
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        # Filter out pytest for check/fmt actions
        return [t for t in available_tools if t != ToolEnum.PYTEST]

    # Parse specific tools
    tool_names: list[str] = [name.strip().upper() for name in tools_str.split(",")]
    tools_to_run: list[ToolEnum] = []

    for name in tool_names:
        # Reject pytest for check/fmt actions
        if name.lower() == ToolName.PYTEST.value:
            raise ValueError(
                "pytest tool is not available for check/fmt actions. "
                "Use 'lintro test' instead.",
            )
        try:
            tool_enum = ToolEnum[name]
            # Verify the tool supports the requested action
            if action == Action.FIX:
                tool_instance = tool_manager.get_tool(tool_enum)
                if not tool_instance.can_fix:
                    raise ValueError(
                        f"Tool '{name.lower()}' does not support formatting",
                    )
            tools_to_run.append(tool_enum)
        except KeyError:
            available_names: list[str] = [
                e.name.lower() for e in ToolEnum if e.name.upper() != "PYTEST"
            ]
            raise ValueError(
                f"Unknown tool '{name.lower()}'. Available tools: {available_names}",
            ) from None

    return tools_to_run


# Tool options parsing moved to tool_options.py


# Output writing functionality moved to output_writers.py


def run_lint_tools_simple(
    *,
    action: str | Action,
    paths: list[str],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
    raw_output: bool = False,
    output_file: str | None = None,
) -> int:
    """Simplified runner using Loguru-based logging with rich formatting.

    Clean approach with beautiful output:
    - SimpleLintroLogger handles ALL console output and file logging with rich
      formatting
    - OutputManager handles structured output files
    - No tee, no complex state management

    Args:
        action: str | Action: Action to perform ("check", "fmt", "test").
        paths: list[str]: List of paths to check.
        tools: str | None: Comma-separated list of tools to run.
        tool_options: str | None: Additional tool options.
        exclude: str | None: Patterns to exclude.
        include_venv: bool: Whether to include virtual environments.
        group_by: str: How to group results.
        output_format: str: Output format for results.
        verbose: bool: Whether to enable verbose output.
        raw_output: bool: Whether to show raw tool output instead of formatted output.
        output_file: str | None: Optional file path to write results to.

    Returns:
        int: Exit code (0 for success, 1 for failures).
    """
    # Normalize action to enum
    action = normalize_action(action)

    # Delegate to the actual implementation in tool_executor.py
    from lintro.utils.tool_executor import (
        run_lint_tools_simple as _run_lint_tools_simple,
    )

    return _run_lint_tools_simple(
        action=action,
        paths=paths,
        tools=tools,
        tool_options=tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
        output_file=output_file,
    )
