"""Doctor command for checking external tool installation status.

This command checks tools that users must install separately (not bundled with lintro).
Bundled Python tools (ruff, black, bandit, mypy, yamllint, darglint) are installed
as dependencies and managed via pyproject.toml - use `pip check` or `uv sync` for those.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

import click
from rich.console import Console
from rich.table import Table

from lintro._tool_versions import TOOL_VERSIONS
from lintro.tools.core.version_parsing import extract_version_from_output

# Map tool names to commands (external tools only)
TOOL_COMMANDS: dict[str, list[str]] = {
    "actionlint": ["actionlint", "--version"],
    "biome": ["biome", "--version"],
    "cargo_audit": ["cargo", "audit", "--version"],
    "clippy": ["cargo", "clippy", "--version"],
    "gitleaks": ["gitleaks", "version"],
    "hadolint": ["hadolint", "--version"],
    "markdownlint": ["markdownlint-cli2", "--version"],
    "prettier": ["prettier", "--version"],
    "pytest": ["python", "-m", "pytest", "--version"],
    "rustfmt": ["rustfmt", "--version"],
    "semgrep": ["semgrep", "--version"],
    "shellcheck": ["shellcheck", "--version"],
    "shfmt": ["shfmt", "--version"],
    "sqlfluff": ["sqlfluff", "--version"],
    "taplo": ["taplo", "--version"],
}


def _check_tool_commands_coverage() -> list[str]:
    """Check for tools in TOOL_VERSIONS that don't have commands defined.

    Returns:
        List of tool names that are in TOOL_VERSIONS but not in TOOL_COMMANDS.
    """
    return [tool for tool in TOOL_VERSIONS if tool not in TOOL_COMMANDS]


def _get_installed_version(tool_name: str) -> str | None:
    """Get the installed version of an external tool.

    Args:
        tool_name: Name of the tool to check.

    Returns:
        Version string if installed, None otherwise.
    """
    command = TOOL_COMMANDS.get(tool_name)
    if not command:
        return None

    # Check if the main executable exists
    main_cmd = command[0]
    if not shutil.which(main_cmd):
        return None

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return extract_version_from_output(output, tool_name)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _compare_versions(installed: str, expected: str) -> str:
    """Compare installed version against expected.

    Args:
        installed: Installed version string.
        expected: Expected minimum version string.

    Returns:
        str: Status string - "ok", "outdated", or "unknown".
    """
    try:
        installed_parts = [int(x) for x in installed.split(".")[:3]]
        expected_parts = [int(x) for x in expected.split(".")[:3]]

        # Pad to equal length
        while len(installed_parts) < 3:
            installed_parts.append(0)
        while len(expected_parts) < 3:
            expected_parts.append(0)

        if installed_parts >= expected_parts:
            return "ok"
        return "outdated"
    except (ValueError, AttributeError):
        # Can't compare versions - treat as unknown rather than silently passing
        return "unknown"


@click.command()
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output as JSON.",
)
@click.option(
    "--tools",
    type=str,
    help="Comma-separated list of tools to check (default: all).",
)
def doctor_command(json_output: bool, tools: str | None) -> None:
    """Check external tool installation status and version compatibility.

    Checks tools that must be installed separately (hadolint, actionlint,
    prettier, etc.). Bundled Python tools are managed via pip/uv.

    Args:
        json_output: If True, output results as JSON.
        tools: Comma-separated list of tools to check, or None for all.

    Raises:
        SystemExit: If there are missing or outdated tools (non-JSON mode).

    Examples:
        lintro doctor
        lintro doctor --tools hadolint,actionlint,prettier
        lintro doctor --json
    """
    console = Console(stderr=True)

    # Warn about tools without command definitions
    uncovered_tools = _check_tool_commands_coverage()
    if uncovered_tools and not json_output:
        console.print(
            f"[yellow]Warning: No version command defined for: "
            f"{', '.join(uncovered_tools)}[/yellow]",
        )

    # Filter tools if specified
    if tools:
        tool_list = [t.strip() for t in tools.split(",")]
        versions_to_check = {k: v for k, v in TOOL_VERSIONS.items() if k in tool_list}
    else:
        versions_to_check = TOOL_VERSIONS

    results: dict[str, dict[str, str | None]] = {}
    ok_count = 0
    missing_count = 0
    outdated_count = 0
    unknown_count = 0

    for tool_name, expected_version in sorted(versions_to_check.items()):
        installed_version = _get_installed_version(tool_name)

        if installed_version is None:
            status = "missing"
            missing_count += 1
        else:
            status = _compare_versions(installed_version, expected_version)
            if status == "ok":
                ok_count += 1
            elif status == "outdated":
                outdated_count += 1
            else:  # unknown
                unknown_count += 1

        results[tool_name] = {
            "expected": expected_version,
            "installed": installed_version,
            "status": status,
        }

    # JSON output mode
    if json_output:
        output = {
            "tools": results,
            "summary": {
                "total": len(results),
                "ok": ok_count,
                "missing": missing_count,
                "outdated": outdated_count,
                "unknown": unknown_count,
            },
        }
        if uncovered_tools:
            output["warnings"] = {
                "uncovered_tools": uncovered_tools,
            }
        click.echo(json.dumps(output, indent=2))
        # Exit non-zero if any tools are missing or outdated
        if missing_count > 0 or outdated_count > 0:
            sys.exit(1)
        return

    # Rich table output
    display_console = Console()

    table = Table(title="Tool Health Check")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Expected", style="dim")
    table.add_column("Installed", style="yellow")
    table.add_column("Status", justify="center")

    for tool_name, info in results.items():
        expected = info["expected"] or "-"
        installed = info["installed"] or "-"

        if info["status"] == "ok":
            status = "[green]✓ OK[/green]"
        elif info["status"] == "missing":
            status = "[red]✗ Missing[/red]"
        elif info["status"] == "outdated":
            status = "[yellow]⚠ Outdated[/yellow]"
        else:  # unknown
            status = "[dim]? Unknown[/dim]"

        table.add_row(tool_name, expected, installed, status)

    display_console.print(table)
    display_console.print()

    # Summary
    total = len(results)
    if missing_count == 0 and outdated_count == 0:
        if unknown_count > 0:
            display_console.print(
                f"[green]✅ {ok_count} tool(s) OK[/green], "
                f"[dim]{unknown_count} with unknown version format[/dim]",
            )
        else:
            display_console.print(
                f"[green]✅ All {total} tools are properly installed.[/green]",
            )
    else:
        if missing_count > 0:
            display_console.print(f"[red]✗ {missing_count} tool(s) missing[/red]")
        if outdated_count > 0:
            display_console.print(
                f"[yellow]⚠ {outdated_count} tool(s) outdated[/yellow]",
            )
        if unknown_count > 0:
            display_console.print(
                f"[dim]? {unknown_count} tool(s) with unknown version format[/dim]",
            )
        display_console.print()
        display_console.print(
            "[dim]Run 'lintro versions --verbose' for installation instructions.[/dim]",
        )

    # Exit with error if any tools are missing or outdated
    if missing_count > 0 or outdated_count > 0:
        raise SystemExit(1)
