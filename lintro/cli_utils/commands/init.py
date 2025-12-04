"""Init command for Lintro.

Creates a .lintro-config.yaml scaffold file with sensible defaults.
"""

from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel

# Default config template
DEFAULT_CONFIG_TEMPLATE = """\
# Lintro Configuration
# https://github.com/TurboCoder13/py-lintro
#
# Lintro acts as the master configuration source for all tools.
# Native tool configs (e.g., .prettierrc) are ignored by default unless
# explicitly referenced via config_source.

global:
  # Line length limit applied to all supporting tools
  # Maps to: ruff line-length, black line-length, prettier printWidth, etc.
  line_length: 88

  # Python version target (e.g., "py313", "py312")
  # Maps to: ruff target-version, black target-version
  target_python: "py313"

execution:
  # List of tools to run (empty = all available tools)
  # enabled_tools: ["ruff", "prettier", "markdownlint", "yamllint"]
  enabled_tools: []

  # Execution order strategy:
  # - "priority": Formatters before linters (default)
  # - "alphabetical": Alphabetical order
  # - ["tool1", "tool2", ...]: Custom order
  tool_order: "priority"

  # Stop on first tool failure
  fail_fast: false

tools:
  # Ruff - Python linter and formatter
  ruff:
    enabled: true
    # config_source: ".ruff.toml"  # Optional: inherit from native config
    # Settings are passed directly to Ruff
    # select: ["E", "F", "W", "I"]
    # ignore: ["E501"]

  # Black - Python formatter
  black:
    enabled: true
    # config_source: "pyproject.toml"  # Optional: use [tool.black] section

  # Prettier - Multi-language formatter
  prettier:
    enabled: true
    # config_source: ".prettierrc"  # Optional: inherit from native config
    # overrides:
    #   printWidth: 88  # Override to match global line_length

  # Markdownlint - Markdown linter
  markdownlint:
    enabled: true
    # MD013 line_length is automatically synced from global.line_length

  # Yamllint - YAML linter
  yamllint:
    enabled: true

  # Bandit - Security linter
  bandit:
    enabled: true

  # Hadolint - Dockerfile linter
  hadolint:
    enabled: true

  # Actionlint - GitHub Actions linter
  actionlint:
    enabled: true

  # Darglint - Docstring linter
  darglint:
    enabled: true
"""

MINIMAL_CONFIG_TEMPLATE = """\
# Lintro Configuration (Minimal)
# https://github.com/TurboCoder13/py-lintro

global:
  line_length: 88
  target_python: "py313"

execution:
  tool_order: "priority"

tools:
  ruff:
    enabled: true
  black:
    enabled: true
  prettier:
    enabled: true
"""


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
    help="Overwrite existing .lintro-config.yaml file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=".lintro-config.yaml",
    help="Output file path (default: .lintro-config.yaml).",
)
def init_command(
    minimal: bool,
    force: bool,
    output: str,
) -> None:
    """Initialize a new .lintro-config.yaml configuration file.

    Creates a scaffold configuration file with sensible defaults.
    Lintro will use this file as the master configuration source,
    ignoring native tool configs unless explicitly referenced.

    Args:
        minimal: Use minimal template with fewer comments.
        force: Overwrite existing config file if it exists.
        output: Output file path for the config file.

    Raises:
        SystemExit: If file exists and --force not provided, or write fails.
    """
    console = Console()
    output_path = Path(output)

    # Check if file already exists
    if output_path.exists() and not force:
        console.print(
            f"[red]Error: {output_path} already exists. "
            "Use --force to overwrite.[/red]",
        )
        raise SystemExit(1)

    # Select template
    template = MINIMAL_CONFIG_TEMPLATE if minimal else DEFAULT_CONFIG_TEMPLATE

    # Write config file
    try:
        output_path.write_text(template, encoding="utf-8")

        # Success panel
        console.print(
            Panel.fit(
                f"[bold green]✅ Created {output_path}[/bold green]",
                border_style="green",
            ),
        )
        console.print()

        # Next steps
        console.print("[bold cyan]Next steps:[/bold cyan]")
        console.print("  [dim]1.[/dim] Review and customize the configuration")
        console.print("  [dim]2.[/dim] Run [cyan]lintro config[/cyan] to verify")
        console.print("  [dim]3.[/dim] Run [cyan]lintro check .[/cyan] to lint")
        logger.debug(f"Created config file: {output_path.resolve()}")

    except (OSError, PermissionError) as e:
        console.print(f"[red]Error: Failed to write {output_path}: {e}[/red]")
        raise SystemExit(1) from e
