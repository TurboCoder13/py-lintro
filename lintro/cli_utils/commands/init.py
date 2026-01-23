"""Init command for Lintro.

Creates configuration files for Lintro and optionally native tool configs.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel

# Default Lintro config template (project-recommended defaults)
DEFAULT_CONFIG_TEMPLATE = """\
# Lintro Configuration
# https://github.com/TurboCoder13/py-lintro
#
# Lintro acts as the master configuration source for all tools.
# Native tool configs are ignored by default unless
# explicitly referenced via config_source.
#
# enforce: Cross-cutting settings injected via CLI flags
# execution: What tools run and how
# defaults: Fallback config when no native config exists
# tools: Per-tool enable/disable and optional config source

enforce:
  # Applied to ruff/black and other tools that honor line length
  line_length: 88
  # Aligns with project requires-python (pyproject.toml)
  target_python: "py313"

execution:
  enabled_tools: []
  tool_order: "priority"
  fail_fast: false

defaults:
  mypy:
    strict: true
    ignore_missing_imports: true

tools:
  ruff:
    enabled: true
  black:
    enabled: true
  mypy:
    enabled: true
  markdownlint:
    enabled: true
  yamllint:
    enabled: true
  bandit:
    enabled: true
  hadolint:
    enabled: true
  actionlint:
    enabled: true
"""

MINIMAL_CONFIG_TEMPLATE = """\
# Lintro Configuration (Minimal)
# https://github.com/TurboCoder13/py-lintro

enforce:
  line_length: 88
  target_python: "py313"

defaults:
  mypy:
    strict: true
    ignore_missing_imports: true

execution:
  tool_order: "priority"

tools:
  ruff:
    enabled: true
  black:
    enabled: true
  mypy:
    enabled: true
"""

# Native config templates
MARKDOWNLINT_TEMPLATE = {
    "config": {
        "MD013": {
            "line_length": 88,
            "code_blocks": False,
            "tables": False,
        },
    },
}


def _write_file(
    path: Path,
    content: str,
    console: Console,
    force: bool,
) -> bool:
    """Write content to a file, handling existing files.

    Args:
        path: Path to write to.
        content: Content to write.
        console: Rich console for output.
        force: Whether to overwrite existing files.

    Returns:
        bool: True if file was written, False if skipped.
    """
    if path.exists() and not force:
        console.print(f"  [yellow]⏭️  Skipped {path} (already exists)[/yellow]")
        return False

    try:
        path.write_text(content, encoding="utf-8")
        console.print(f"  [green]✅ Created {path}[/green]")
        return True
    except (OSError, Exception) as e:
        console.print(f"  [red]❌ Failed to write {path}: {e}[/red]")
        return False


def _write_json_file(
    path: Path,
    data: Mapping[str, Any],
    console: Console,
    force: bool,
) -> bool:
    """Write JSON content to a file, handling existing files.

    Args:
        path: Path to write to.
        data: Dictionary to serialize as JSON.
        console: Rich console for output.
        force: Whether to overwrite existing files.

    Returns:
        bool: True if file was written, False if skipped.
    """
    content = json.dumps(obj=data, indent=2) + "\n"
    return _write_file(path=path, content=content, console=console, force=force)


def _generate_native_configs(
    console: Console,
    force: bool,
) -> list[str]:
    """Generate native tool configuration files.

    Args:
        console: Rich console for output.
        force: Whether to overwrite existing files.

    Returns:
        list[str]: List of created file names.
    """
    created: list[str] = []

    console.print("\n[bold cyan]Generating native tool configs:[/bold cyan]")

    # Markdownlint config
    if _write_json_file(
        path=Path(".markdownlint-cli2.jsonc"),
        data=MARKDOWNLINT_TEMPLATE,
        console=console,
        force=force,
    ):
        created.append(".markdownlint-cli2.jsonc")

    return created


@click.command("init")
@click.option(
    "--minimal",
    "-m",
    is_flag=True,
    help="Create a minimal config file with fewer comments.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing configuration files.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=".lintro-config.yaml",
    help="Output file path (default: .lintro-config.yaml).",
)
@click.option(
    "--with-native-configs",
    is_flag=True,
    help="Also generate native tool configs (.markdownlint-cli2.jsonc, etc.).",
)
def init_command(
    minimal: bool,
    force: bool,
    output: str,
    with_native_configs: bool,
) -> None:
    """Initialize Lintro configuration for your project.

    Creates a scaffold configuration file with sensible defaults.
    Lintro will use this file as the master configuration source,
    ignoring native tool configs unless explicitly referenced.

    Use --with-native-configs to also generate native tool configuration
    files for IDE integration (e.g., markdownlint extension).

    Args:
        minimal: Use minimal template with fewer comments.
        force: Overwrite existing config file if it exists.
        output: Output file path for the config file.
        with_native_configs: Also generate native tool config files.

    Raises:
        SystemExit: If file exists and --force not provided, or write fails.
    """
    console = Console()
    output_path = Path(output)
    created_files: list[str] = []

    # Check if main config file already exists
    if output_path.exists() and not force:
        console.print(
            f"[red]Error: {output_path} already exists. "
            "Use --force to overwrite.[/red]",
        )
        raise SystemExit(1)

    # Select template
    template = MINIMAL_CONFIG_TEMPLATE if minimal else DEFAULT_CONFIG_TEMPLATE

    # Write main config file
    try:
        output_path.write_text(template, encoding="utf-8")
        created_files.append(str(output_path))
        logger.debug(f"Created config file: {output_path.resolve()}")

    except (OSError, PermissionError) as e:
        console.print(f"[red]Error: Failed to write {output_path}: {e}[/red]")
        raise SystemExit(1) from e

    # Generate native configs if requested
    if with_native_configs:
        native_files = _generate_native_configs(console=console, force=force)
        created_files.extend(native_files)

    # Success panel
    console.print()
    if len(created_files) == 1:
        console.print(
            Panel.fit(
                f"[bold green]✅ Created {output_path}[/bold green]",
                border_style="green",
            ),
        )
    else:
        files_list = "\n".join(f"  • {f}" for f in created_files)
        msg = f"[bold green]✅ Created {len(created_files)} files:[/bold green]"
        console.print(
            Panel.fit(
                f"{msg}\n{files_list}",
                border_style="green",
            ),
        )

    console.print()

    # Next steps
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print("  [dim]1.[/dim] Review and customize the configuration")
    console.print(
        "  [dim]2.[/dim] Run [cyan]lintro config[/cyan] to view config",
    )
    console.print("  [dim]3.[/dim] Run [cyan]lintro check .[/cyan] to lint")
    if with_native_configs:
        console.print(
            "  [dim]3.[/dim] Commit the config files to your repository",
        )
