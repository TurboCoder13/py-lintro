"""Init command for Lintro.

Creates configuration files for Lintro and optionally native tool configs.
"""

import json
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel

# Default Lintro config template
DEFAULT_CONFIG_TEMPLATE = """\
# Lintro Configuration
# https://github.com/TurboCoder13/py-lintro
#
# Lintro acts as the master configuration source for all tools.
# Native tool configs (e.g., .prettierrc) are ignored by default unless
# explicitly referenced via config_source.

enforce:
  # Line length limit applied to all supporting tools
  # Maps to: ruff line-length, black line-length, prettier printWidth, etc.
  line_length: 88

  # Python version target (e.g., "py313", "py312", "py310")
  # Maps to: ruff target-version, black target-version
  # Omit to let tools infer from requires-python in pyproject.toml
  # target_python: "py310"

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
    #   printWidth: 88  # Override to match enforce line_length

  # Markdownlint - Markdown linter
  markdownlint:
    enabled: true
    # MD013 line_length is automatically synced from enforce.line_length

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

enforce:
  line_length: 88
  # target_python: "py310"  # Omit to infer from requires-python

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

# Native config templates
PRETTIERRC_TEMPLATE = {
    "semi": True,
    "singleQuote": True,
    "tabWidth": 2,
    "printWidth": 88,
    "trailingComma": "es5",
    "proseWrap": "always",
    "overrides": [
        {
            "files": "*.md",
            "options": {
                "printWidth": 88,
                "proseWrap": "always",
            },
        },
    ],
}

PRETTIERIGNORE_TEMPLATE = """\
# Ignore artifacts
build
dist
node_modules
.venv
.lintro
"""

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
    data: dict,
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

    # Prettier config
    if _write_json_file(
        path=Path(".prettierrc.json"),
        data=PRETTIERRC_TEMPLATE,
        console=console,
        force=force,
    ):
        created.append(".prettierrc.json")

    # Prettier ignore
    if _write_file(
        path=Path(".prettierignore"),
        content=PRETTIERIGNORE_TEMPLATE,
        console=console,
        force=force,
    ):
        created.append(".prettierignore")

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
    help="Also generate native tool configs (.prettierrc.json, etc.).",
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
    files for IDE integration (e.g., Prettier extension, markdownlint extension).

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
    console.print("  [dim]2.[/dim] Run [cyan]lintro check .[/cyan] to lint")
    if with_native_configs:
        console.print(
            "  [dim]3.[/dim] Commit the config files to your repository",
        )
