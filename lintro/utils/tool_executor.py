"""Simplified runner for lintro commands.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. SimpleLintroLogger - handles console display AND logging with Loguru + rich
   formatting
3. No tee, no stream redirection, no complex state management
"""

from lintro.enums.group_by import GroupBy, normalize_group_by
from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.config import (
    _load_ruff_config,
    load_lintro_tool_config,
    load_post_checks_config,
)
from lintro.utils.console_logger import create_logger
from lintro.utils.output_manager import OutputManager
from lintro.utils.tool_utils import format_tool_output

# Constants
DEFAULT_EXIT_CODE_SUCCESS: int = 0
DEFAULT_EXIT_CODE_FAILURE: int = 1
DEFAULT_REMAINING_COUNT: int = 1

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
    tools: str | None,
    action: str,
) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: str | None: Comma-separated tool names, "all", or None.
        action: str: "check", "fmt", or "test".

    Returns:
        list[ToolEnum]: List of ToolEnum instances to run.

    Raises:
        ValueError: If unknown tool names are provided.
    """
    if action == "test":
        # Test action only supports pytest
        if tools and tools.lower() != "pytest":
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

    if tools == "all" or tools is None:
        # Get all available tools for the action
        if action == "fmt":
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        # Filter out pytest for check/fmt actions
        return [t for t in available_tools if t.name.upper() != "PYTEST"]

    # Parse specific tools
    tool_names: list[str] = [name.strip().upper() for name in tools.split(",")]
    tools_to_run: list[ToolEnum] = []

    for name in tool_names:
        # Reject pytest for check/fmt actions
        if name == "PYTEST":
            raise ValueError(
                "pytest tool is not available for check/fmt actions. "
                "Use 'lintro test' instead.",
            )
        try:
            tool_enum = ToolEnum[name]
            # Verify the tool supports the requested action
            if action == "fmt":
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


def _coerce_value(raw: str) -> object:
    """Coerce a raw CLI value into a typed Python value.

    Rules:
    - "all"/"none" (case-insensitive) -> list[str]
    - "True"/"False" (case-insensitive) -> bool
    - "None"/"null" (case-insensitive) -> None
    - integer (e.g., 88) -> int
    - float (e.g., 0.75) -> float
    - list via pipe-delimited values (e.g., "E|F|W") -> list[str]
      Pipe is chosen to avoid conflict with the top-level comma separator.
    - otherwise -> original string

    Args:
        raw: str: Raw CLI value to coerce.

    Returns:
        object: Coerced value.
    """
    s = raw.strip()
    # Lists via pipe (e.g., select=E|F)
    if "|" in s:
        return [part.strip() for part in s.split("|") if part.strip()]

    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"none", "null"}:
        return None

    # Try int
    try:
        return int(s)
    except ValueError:
        pass

    # Try float
    try:
        return float(s)
    except ValueError:
        pass

    return s


def _parse_tool_options(tool_options: str | None) -> dict[str, dict[str, object]]:
    """Parse tool options string into a typed dictionary.

    Args:
        tool_options: str | None: String in format
            "tool:option=value,tool2:option=value". Multiple values for a single
            option can be provided using pipe separators (e.g., select=E|F).

    Returns:
        dict[str, dict[str, object]]: Mapping tool names to typed options.
    """
    if not tool_options:
        return {}

    tool_option_dict: dict[str, dict[str, object]] = {}
    for opt in tool_options.split(","):
        opt = opt.strip()
        if not opt:
            continue
        if ":" not in opt:
            # Skip malformed fragment
            continue
        tool_name, tool_opt = opt.split(":", 1)
        if "=" not in tool_opt:
            # Skip malformed fragment
            continue
        opt_name, opt_value = tool_opt.split("=", 1)
        tool_name = tool_name.strip().lower()
        opt_name = opt_name.strip()
        opt_value = opt_value.strip()
        if not tool_name or not opt_name:
            continue
        if tool_name not in tool_option_dict:
            tool_option_dict[tool_name] = {}
        tool_option_dict[tool_name][opt_name] = _coerce_value(opt_value)

    return tool_option_dict


def _write_output_file(
    *,
    output_path: str,
    output_format: OutputFormat,
    all_results: list,
    action: str,
    total_issues: int,
    total_fixed: int,
) -> None:
    """Write results to user-specified output file.

    Args:
        output_path: str: Path to the output file.
        output_format: OutputFormat: Format for the output.
        all_results: list: List of ToolResult objects.
        action: str: The action performed (check, fmt, test).
        total_issues: int: Total number of issues found.
        total_fixed: int: Total number of issues fixed.
    """
    import csv
    import datetime
    import json
    from pathlib import Path

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_format == OutputFormat.JSON:
        # Build JSON structure similar to stdout JSON mode
        json_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "summary": {
                "total_issues": total_issues,
                "total_fixed": total_fixed,
                "tools_run": len(all_results),
            },
            "results": [],
        }
        for result in all_results:
            result_data = {
                "tool": result.name,
                "success": getattr(result, "success", True),
                "issues_count": getattr(result, "issues_count", 0),
                "output": getattr(result, "output", ""),
            }
            if hasattr(result, "issues") and result.issues:
                result_data["issues"] = [
                    {
                        "file": getattr(issue, "file", ""),
                        "line": getattr(issue, "line", ""),
                        "code": getattr(issue, "code", ""),
                        "message": getattr(issue, "message", ""),
                    }
                    for issue in result.issues
                ]
            json_data["results"].append(result_data)
        output_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    elif output_format == OutputFormat.CSV:
        # Write CSV format
        rows: list[list[str]] = []
        header: list[str] = ["tool", "issues_count", "file", "line", "code", "message"]
        for result in all_results:
            if hasattr(result, "issues") and result.issues:
                for issue in result.issues:
                    rows.append(
                        [
                            result.name,
                            str(getattr(result, "issues_count", 0)),
                            str(getattr(issue, "file", "")),
                            str(getattr(issue, "line", "")),
                            str(getattr(issue, "code", "")),
                            str(getattr(issue, "message", "")),
                        ],
                    )
            else:
                rows.append(
                    [
                        result.name,
                        str(getattr(result, "issues_count", 0)),
                        "",
                        "",
                        "",
                        "",
                    ],
                )
        with output_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    elif output_format == OutputFormat.MARKDOWN:
        # Write Markdown format
        lines: list[str] = ["# Lintro Report", ""]
        lines.append("## Summary\n")
        lines.append("| Tool | Issues |")
        lines.append("|------|--------|")
        for result in all_results:
            lines.append(f"| {result.name} | {getattr(result, 'issues_count', 0)} |")
        lines.append("")
        for result in all_results:
            issues_count = getattr(result, "issues_count", 0)
            lines.append(f"### {result.name} ({issues_count} issues)")
            if hasattr(result, "issues") and result.issues:
                lines.append("| File | Line | Code | Message |")
                lines.append("|------|------|------|---------|")
                for issue in result.issues:
                    file_val = str(getattr(issue, "file", "")).replace("|", r"\|")
                    line_val = getattr(issue, "line", "")
                    code_val = str(getattr(issue, "code", "")).replace("|", r"\|")
                    msg_val = str(getattr(issue, "message", "")).replace("|", r"\|")
                    lines.append(
                        f"| {file_val} | {line_val} | {code_val} | {msg_val} |",
                    )
                lines.append("")
            else:
                lines.append("No issues found.\n")
        output_file.write_text("\n".join(lines), encoding="utf-8")

    elif output_format == OutputFormat.HTML:
        # Write HTML format
        html_lines: list[str] = [
            "<html><head><title>Lintro Report</title></head><body>",
        ]
        html_lines.append("<h1>Lintro Report</h1>")
        html_lines.append("<h2>Summary</h2>")
        html_lines.append("<table border='1'><tr><th>Tool</th><th>Issues</th></tr>")
        for result in all_results:
            import html

            safe_name = html.escape(result.name)
            html_lines.append(
                f"<tr><td>{safe_name}</td>"
                f"<td>{getattr(result, 'issues_count', 0)}</td></tr>",
            )
        html_lines.append("</table>")
        for result in all_results:
            import html

            issues_count = getattr(result, "issues_count", 0)
            html_lines.append(
                f"<h3>{html.escape(result.name)} ({issues_count} issues)</h3>",
            )
            if hasattr(result, "issues") and result.issues:
                html_lines.append(
                    "<table border='1'><tr><th>File</th><th>Line</th>"
                    "<th>Code</th><th>Message</th></tr>",
                )
                for issue in result.issues:
                    f_val = html.escape(str(getattr(issue, "file", "")))
                    l_val = getattr(issue, "line", "")
                    c_val = html.escape(str(getattr(issue, "code", "")))
                    m_val = html.escape(str(getattr(issue, "message", "")))
                    html_lines.append(
                        f"<tr><td>{f_val}</td><td>{l_val}</td>"
                        f"<td>{c_val}</td><td>{m_val}</td></tr>",
                    )
                html_lines.append("</table>")
            else:
                html_lines.append("<p>No issues found.</p>")
        html_lines.append("</body></html>")
        output_file.write_text("\n".join(html_lines), encoding="utf-8")

    else:
        # Plain or Grid format - write formatted text output
        lines: list[str] = [f"Lintro {action.capitalize()} Report", "=" * 40, ""]
        for result in all_results:
            issues_count = getattr(result, "issues_count", 0)
            lines.append(f"{result.name}: {issues_count} issues")
            output_text = getattr(result, "output", "")
            if output_text and output_text.strip():
                lines.append(output_text.strip())
            lines.append("")
        lines.append(f"Total Issues: {total_issues}")
        if action == "fmt":
            lines.append(f"Total Fixed: {total_fixed}")
        output_file.write_text("\n".join(lines), encoding="utf-8")


def run_lint_tools_simple(
    *,
    action: str,
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
        action: str: "check" or "fmt".
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
    # Initialize output manager for this run
    output_manager = OutputManager()
    run_dir: str = output_manager.run_dir

    # Create simplified logger with rich formatting
    logger = create_logger(run_dir=run_dir, verbose=verbose, raw_output=raw_output)

    logger.debug(f"Starting {action} command")
    logger.debug(f"Paths: {paths}")
    logger.debug(f"Tools: {tools}")
    logger.debug(f"Run directory: {run_dir}")

    # For JSON output format, we'll collect results and output JSON at the end
    # Normalize enums while maintaining backward compatibility
    output_fmt_enum: OutputFormat = normalize_output_format(output_format)
    group_by_enum: GroupBy = normalize_group_by(group_by)
    json_output_mode = output_fmt_enum == OutputFormat.JSON

    try:
        # Get tools to run
        try:
            tools_to_run = _get_tools_to_run(tools=tools, action=action)
        except ValueError as e:
            logger.error(str(e))
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        if not tools_to_run:
            logger.warning("No tools found to run")
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        # Parse tool options
        tool_option_dict = _parse_tool_options(tool_options)

        # Load post-checks config early to exclude those tools from main phase
        post_cfg_early = load_post_checks_config()
        post_enabled_early = bool(post_cfg_early.get("enabled", False))
        post_tools_early: set[str] = (
            {t.lower() for t in (post_cfg_early.get("tools", []) or [])}
            if post_enabled_early
            else set()
        )

        if post_tools_early:
            tools_to_run = [
                t for t in tools_to_run if t.name.lower() not in post_tools_early
            ]

        # If early post-check filtering removed all tools from the main phase,
        # return a failure to signal that nothing was executed in the main run.
        if not tools_to_run:
            logger.warning(
                "All selected tools were filtered out by post-check configuration",
            )
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        # Print main header (skip for JSON mode)
        tools_list: str = ", ".join(t.name.lower() for t in tools_to_run)
        if not json_output_mode:
            logger.print_lintro_header(
                action=action,
                tool_count=len(tools_to_run),
                tools_list=tools_list,
            )

            # Print verbose info if requested
            paths_list: str = ", ".join(paths)
            logger.print_verbose_info(
                action=action,
                tools_list=tools_list,
                paths_list=paths_list,
                output_format=output_format,
            )

        all_results: list = []
        total_issues: int = 0
        total_fixed: int = 0
        total_remaining: int = 0

        # Run each tool with rich formatting
        for tool_enum in tools_to_run:
            # Resolve the tool instance; if unavailable, record failure and continue
            try:
                tool = tool_manager.get_tool(tool_enum)
            except Exception as e:
                tool_name: str = _get_tool_display_name(tool_enum)
                logger.warning(f"Tool '{tool_name}' unavailable: {e}")
                from lintro.models.core.tool_result import ToolResult

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )
                continue

            # Use canonical display name for consistent logging
            tool_name: str = _get_tool_display_name(tool_enum)
            # Print rich tool header (skip for JSON mode)
            if not json_output_mode:
                logger.print_tool_header(tool_name=tool_name, action=action)

            try:
                # Configure tool options
                # 1) Load config from pyproject.toml / lintro.toml
                cfg: dict = load_lintro_tool_config(tool_name)
                if cfg:
                    try:
                        tool.set_options(**cfg)
                    except Exception as e:
                        logger.debug(f"Ignoring invalid config for {tool_name}: {e}")
                # 2) CLI --tool-options overrides config file
                # Check both tool display name and enum name
                cli_overrides: dict[str, object] = {}
                lookup_keys = _get_tool_lookup_keys(tool_enum, tool_name)
                for option_key in lookup_keys:
                    overrides = tool_option_dict.get(option_key)
                    if overrides:
                        cli_overrides.update(overrides)

                if cli_overrides:
                    tool.set_options(**cli_overrides)

                # Set common options
                if exclude:
                    exclude_patterns: list[str] = [
                        pattern.strip() for pattern in exclude.split(",")
                    ]
                    tool.set_options(exclude_patterns=exclude_patterns)

                tool.set_options(include_venv=include_venv)

                # If Black is configured as a post-check, avoid double formatting by
                # disabling Ruff's formatting stages unless explicitly overridden via
                # CLI or config. This keeps Ruff focused on lint fixes while Black
                # handles formatting.
                if "black" in post_tools_early and tool_name == "ruff":
                    # Respect explicit overrides from CLI or config
                    cfg_overrides = cfg or {}
                    if action == "fmt":
                        if (
                            "format" not in cli_overrides
                            and "format" not in cfg_overrides
                        ):
                            tool.set_options(format=False)
                    else:  # check
                        if (
                            "format_check" not in cli_overrides
                            and "format_check" not in cfg_overrides
                        ):
                            tool.set_options(format_check=False)

                # Run the tool
                logger.debug(f"Executing {tool_name}")

                if action == "fmt":
                    # Respect tool defaults; allow overrides via --tool-options
                    result = tool.fix(paths=paths)
                    # Prefer standardized counters when present
                    fixed_count: int = (
                        getattr(result, "fixed_issues_count", None)
                        if hasattr(result, "fixed_issues_count")
                        else None
                    )
                    if fixed_count is None:
                        fixed_count = 0
                    total_fixed += fixed_count

                    remaining_count: int = (
                        getattr(result, "remaining_issues_count", None)
                        if hasattr(result, "remaining_issues_count")
                        else None
                    )
                    if remaining_count is None:
                        # Fallback to issues_count if standardized field absent
                        remaining_count = getattr(result, "issues_count", 0)
                    total_remaining += max(0, remaining_count)

                    # For display in per-tool logger call below
                    issues_count: int = remaining_count
                else:  # check
                    result = tool.check(paths=paths)
                    issues_count = getattr(result, "issues_count", 0)
                    total_issues += issues_count

                # Format and display output
                output = getattr(result, "output", None)
                issues = getattr(result, "issues", None)
                formatted_output: str = ""

                # Call format_tool_output if we have output or issues
                if (output and output.strip()) or issues:
                    formatted_output = format_tool_output(
                        tool_name=tool_name,
                        output=output or "",
                        group_by=group_by_enum.value,
                        output_format=output_fmt_enum.value,
                        issues=issues,
                    )

                # Print tool results with rich formatting (skip for JSON mode)
                if not json_output_mode:
                    # Use raw output if raw_output is true, otherwise use
                    # formatted output
                    display_output = output if raw_output else formatted_output
                    logger.print_tool_result(
                        tool_name=tool_name,
                        output=display_output,
                        issues_count=issues_count,
                        raw_output_for_meta=output,
                        action=action,
                        success=getattr(result, "success", None),
                    )

                # Store result
                all_results.append(result)

                if action == "fmt":
                    # Pull standardized counts again for debug log
                    fixed_dbg = getattr(result, "fixed_issues_count", fixed_count)
                    remaining_dbg = getattr(
                        result,
                        "remaining_issues_count",
                        issues_count,
                    )
                    logger.debug(
                        f"Completed {tool_name}: {fixed_dbg} fixed, "
                        f"{remaining_dbg} remaining",
                    )
                else:
                    logger.debug(f"Completed {tool_name}: {issues_count} issues found")

            except Exception as e:
                logger.error(f"Error running {tool_name}: {e}")
                # Record a failure result and continue so that structured output
                # (e.g., JSON) is still produced even if a tool cannot be
                # resolved or executed. This keeps behavior consistent with tests
                # that validate JSON output presence independent of exit codes.
                from lintro.models.core.tool_result import ToolResult

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )
                # Continue to next tool rather than aborting the entire run
                continue

        # Optionally run post-checks (explicit, after main tools)
        # Skip post-checks for test action - test commands should only run tests
        if action == "test":
            post_tools = []
            enforce_failure = False
        else:
            post_cfg = post_cfg_early or load_post_checks_config()
            post_enabled = bool(post_cfg.get("enabled", False))
            post_tools = list(post_cfg.get("tools", [])) if post_enabled else []
            enforce_failure = bool(post_cfg.get("enforce_failure", action == "check"))

        # In JSON mode, we still need exit-code enforcement even if we skip
        # rendering post-check outputs. If a post-check tool is unavailable
        # and enforce_failure is enabled during check, append a failure result
        # so summaries and exit codes reflect the condition.
        if post_tools and json_output_mode and action == "check" and enforce_failure:
            for post_tool_name in post_tools:
                try:
                    tool_enum = ToolEnum[post_tool_name.upper()]
                    # Ensure tool can be resolved; we don't execute it in JSON mode
                    _ = tool_manager.get_tool(tool_enum)
                except Exception as e:
                    from lintro.models.core.tool_result import ToolResult

                    all_results.append(
                        ToolResult(
                            name=post_tool_name,
                            success=False,
                            output=str(e),
                            issues_count=1,
                        ),
                    )

        if post_tools and not json_output_mode:
            # Print a clear post-checks section header
            logger.print_post_checks_header(action=action)

            for post_tool_name in post_tools:
                try:
                    tool_enum = ToolEnum[post_tool_name.upper()]
                except KeyError:
                    logger.warning(f"Unknown post-check tool: {post_tool_name}")
                    continue

                # If the tool isn't available in the current environment (e.g., unit
                # tests that stub a limited set of tools), skip without enforcing
                # failure. Post-checks are optional when the tool cannot be resolved
                # from the tool manager.
                try:
                    tool = tool_manager.get_tool(tool_enum)
                except Exception as e:
                    logger.warning(
                        f"Post-check '{post_tool_name}' unavailable: {e}",
                    )
                    continue
                # Use canonical display name for consistent logging
                tool_name = _get_tool_display_name(tool_enum)

                # Post-checks run with explicit headers (reuse standard header)
                if not json_output_mode:
                    logger.print_tool_header(tool_name=tool_name, action=action)

                try:
                    # Load tool-specific config and common options
                    cfg: dict = load_lintro_tool_config(tool_name)
                    if cfg:
                        try:
                            tool.set_options(**cfg)
                        except Exception as e:
                            logger.debug(
                                f"Ignoring invalid config for {tool_name}: {e}",
                            )

                    # Sync Ruff's line_length to Black when Black is a post-check
                    # This ensures Black uses the same line length as Ruff
                    # for consistency
                    # Note: Black may not be able to wrap all lines that Ruff
                    # flags (Black is conservative and only wraps when safe),
                    # but we ensure they use the same line length setting so
                    # Black can attempt to fix what it can.
                    if (
                        tool_name == "black"
                        and "black" in post_tools_early
                        and "line_length" not in cfg
                        and "line-length" not in cfg
                    ):
                        # Sync Ruff's line_length to Black if not explicitly
                        # configured in Black's lintro config
                        # Priority: [tool.lintro.black] > Ruff sync >
                        # Black native config
                        # (CLI args override config file, so this ensures
                        # Black uses Ruff's value when Black has no explicit
                        # line_length in its lintro config)
                        ruff_config = _load_ruff_config()
                        ruff_line_length = ruff_config.get(
                            "line-length",
                        ) or ruff_config.get("line_length")
                        if ruff_line_length is not None:
                            try:
                                tool.set_options(line_length=ruff_line_length)
                                logger.debug(
                                    (
                                        f"Synced Ruff line_length "
                                        f"({ruff_line_length}) to Black"
                                    ),
                                )
                            except Exception as e:
                                logger.debug(
                                    f"Failed to sync Ruff line_length "
                                    f"to Black: {e}",
                                )

                    tool.set_options(include_venv=include_venv)
                    if exclude:
                        exclude_patterns: list[str] = [
                            p.strip() for p in exclude.split(",")
                        ]
                        tool.set_options(exclude_patterns=exclude_patterns)

                    # For check: Black should run in check mode; for fmt: run fix
                    if action == "fmt" and tool.can_fix:
                        result = tool.fix(paths=paths)
                        issues_count = getattr(result, "issues_count", 0)
                        total_fixed += getattr(result, "fixed_issues_count", 0) or 0
                        total_remaining += (
                            getattr(result, "remaining_issues_count", issues_count) or 0
                        )
                    else:
                        result = tool.check(paths=paths)
                        issues_count = getattr(result, "issues_count", 0)
                        total_issues += issues_count

                    # Format and display output
                    output = getattr(result, "output", None)
                    issues = getattr(result, "issues", None)
                    formatted_output: str = ""
                    if (output and output.strip()) or issues:
                        formatted_output = format_tool_output(
                            tool_name=tool_name,
                            output=output or "",
                            group_by=group_by_enum.value,
                            output_format=output_fmt_enum.value,
                            issues=issues,
                        )

                    if not json_output_mode:
                        logger.print_tool_result(
                            tool_name=tool_name,
                            output=(output if raw_output else formatted_output),
                            issues_count=issues_count,
                            raw_output_for_meta=output,
                            action=action,
                            success=getattr(result, "success", None),
                        )

                    all_results.append(result)
                except Exception as e:
                    # Do not crash the entire run due to missing optional post-check
                    # tool
                    logger.warning(f"Post-check '{post_tool_name}' failed: {e}")
                    # Only enforce failure when the tool was available and executed
                    if enforce_failure and action == "check":
                        from lintro.models.core.tool_result import ToolResult

                        all_results.append(
                            ToolResult(
                                name=post_tool_name,
                                success=False,
                                output=str(e),
                                issues_count=1,
                            ),
                        )

        # Handle output based on format
        if json_output_mode:
            # For JSON output, print JSON directly to stdout
            import datetime
            import json

            # Create a simple JSON structure with all results
            json_data = {
                "action": action,
                "timestamp": datetime.datetime.now().isoformat(),
                "tools": [result.name for result in all_results],
                "total_issues": sum(
                    getattr(result, "issues_count", 0) for result in all_results
                ),
                "total_fixed": (
                    sum((getattr(r, "fixed_issues_count", 0) or 0) for r in all_results)
                    if action == "fmt"
                    else None
                ),
                "total_remaining": (
                    sum(
                        (getattr(r, "remaining_issues_count", 0) or 0)
                        for r in all_results
                    )
                    if action == "fmt"
                    else None
                ),
                "results": [],
            }

            for result in all_results:
                result_data = {
                    "tool": result.name,
                    "success": getattr(result, "success", True),
                    "issues_count": getattr(result, "issues_count", 0),
                    "output": getattr(result, "output", ""),
                    "initial_issues_count": getattr(
                        result,
                        "initial_issues_count",
                        None,
                    ),
                    "fixed_issues_count": getattr(result, "fixed_issues_count", None),
                    "remaining_issues_count": getattr(
                        result,
                        "remaining_issues_count",
                        None,
                    ),
                }
                json_data["results"].append(result_data)

            print(json.dumps(json_data, indent=2))
        else:
            # Print rich execution summary with table and ASCII art
            logger.print_execution_summary(action=action, tool_results=all_results)

        # Save outputs
        try:
            output_manager.write_reports_from_results(results=all_results)
            logger.save_console_log()
            logger.debug("Saved all output files")
        except Exception as e:
            # Log at debug to avoid failing the run for non-critical persistence.
            logger.debug(f"Error saving outputs: {e}")

        # Write to user-specified output file if provided
        if output_file:
            try:
                _write_output_file(
                    output_path=output_file,
                    output_format=output_fmt_enum,
                    all_results=all_results,
                    action=action,
                    total_issues=total_issues,
                    total_fixed=total_fixed,
                )
                logger.debug(f"Wrote results to {output_file}")
            except Exception as e:
                logger.error(f"Failed to write output to {output_file}: {e}")

        # Return appropriate exit code
        if action == "fmt":
            # Format operations should fail if:
            # 1. Any tool reported failure (execution error)
            # 2. There are remaining unfixable issues after formatting
            any_failed: bool = any(
                not getattr(result, "success", True) for result in all_results
            )
            # Check if there are remaining issues that couldn't be fixed
            has_remaining_issues: bool = total_remaining > 0
            return (
                DEFAULT_EXIT_CODE_SUCCESS
                if (not any_failed and not has_remaining_issues)
                else DEFAULT_EXIT_CODE_FAILURE
            )
        else:  # check
            # Check operations fail if issues are found OR any tool reported failure
            any_failed: bool = any(
                not getattr(result, "success", True) for result in all_results
            )
            return (
                DEFAULT_EXIT_CODE_SUCCESS
                if (total_issues == 0 and not any_failed)
                else DEFAULT_EXIT_CODE_FAILURE
            )

    except Exception as e:
        logger.debug(f"Unexpected error: {e}")
        logger.save_console_log()
        return DEFAULT_EXIT_CODE_FAILURE
