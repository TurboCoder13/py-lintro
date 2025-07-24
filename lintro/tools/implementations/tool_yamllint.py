"""Yamllint YAML linter integration."""

import subprocess
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes


@dataclass
class YamllintTool(BaseTool):
    """Yamllint YAML linter integration.

    Yamllint is a linter for YAML files that checks for syntax errors,
    formatting issues, and other YAML best practices.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "yamllint"
    description: str = "YAML linter for syntax and style checking"
    can_fix: bool = False  # Yamllint only checks, doesn't fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=40,  # Medium-low priority for configuration linting
            conflicts_with=[],  # No direct conflicts
            file_patterns=[
                "*.yml",
                "*.yaml",
                ".yamllint",
                ".yamllint.yml",
                ".yamllint.yaml",
            ],
            tool_type=ToolType.LINTER,
            options={
                "timeout": 15,  # Default timeout in seconds
                "format": "parsable",  # Output format (parsable, standard, colored, github, auto)
                "config_file": None,  # Path to yamllint config file
                "config_data": None,  # Inline config data
                "strict": False,  # Return non-zero exit code on warnings as well as errors
                "relaxed": False,  # Use relaxed configuration
                "no_warnings": False,  # Output only error level problems
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool."""
        super().__post_init__()

    def set_options(
        self,
        format: str | None = None,
        config_file: str | None = None,
        config_data: str | None = None,
        strict: bool | None = None,
        relaxed: bool | None = None,
        no_warnings: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Yamllint-specific options.

        Args:
            format: Output format (parsable, standard, colored, github, auto)
            config_file: Path to yamllint config file
            config_data: Inline config data (YAML string)
            strict: Return non-zero exit code on warnings as well as errors
            relaxed: Use relaxed configuration
            no_warnings: Output only error level problems
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if format is not None and format not in [
            "parsable",
            "standard",
            "colored",
            "github",
            "auto",
        ]:
            raise ValueError(
                f"Invalid format '{format}'. Must be one of: "
                "parsable, standard, colored, github, auto"
            )

        if config_file is not None and not isinstance(config_file, str):
            raise ValueError("config_file must be a string path")

        if config_data is not None and not isinstance(config_data, str):
            raise ValueError("config_data must be a YAML string")

        if strict is not None and not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")

        if relaxed is not None and not isinstance(relaxed, bool):
            raise ValueError("relaxed must be a boolean")

        if no_warnings is not None and not isinstance(no_warnings, bool):
            raise ValueError("no_warnings must be a boolean")

        options = {
            "format": format,
            "config_file": config_file,
            "config_data": config_data,
            "strict": strict,
            "relaxed": relaxed,
            "no_warnings": no_warnings,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the yamllint command.

        Returns:
            List of command arguments
        """
        cmd = ["yamllint"]

        # Add format option
        format_option = self.options.get("format", "parsable")
        cmd.extend(["--format", format_option])

        # Add config file
        config_file = self.options.get("config_file")
        if config_file:
            cmd.extend(["--config-file", config_file])

        # Add config data (inline config)
        config_data = self.options.get("config_data")
        if config_data:
            cmd.extend(["--config-data", config_data])

        # Add strict mode
        if self.options.get("strict", False):
            cmd.append("--strict")

        # Add relaxed mode
        if self.options.get("relaxed", False):
            cmd.append("--relaxed")

        # Add no-warnings option
        if self.options.get("no_warnings", False):
            cmd.append("--no-warnings")

        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Yamllint.

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        yaml_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        logger.debug(f"Files to check: {yaml_files}")

        timeout = self.options.get("timeout", 15)
        all_outputs = []
        all_success = True
        skipped_files = []
        total_issues = 0

        for file_path in yaml_files:
            cmd = self._build_command() + [str(file_path)]
            try:
                success, output = self._run_subprocess(cmd, timeout=timeout)
                issues = parse_yamllint_output(output)
                issues_count = len(issues)
                if not (success and issues_count == 0):
                    all_success = False
                total_issues += issues_count
                if output.strip():
                    all_outputs.append(output)
            except subprocess.TimeoutExpired:
                skipped_files.append(file_path)
                all_success = False
            except Exception as e:
                all_outputs.append(f"Error processing {file_path}: {str(e)}")
                all_success = False

        output = "\n".join(all_outputs) if all_outputs else ""
        if skipped_files:
            if output:
                output += "\n\n"
            output += f"Skipped {len(skipped_files)} files due to timeout:"
            for file in skipped_files:
                output += f"\n  - {file}"

        if not output.strip():
            output = None

        return ToolResult(
            name=self.name,
            success=all_success,
            output=output,
            issues_count=total_issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files with Yamllint.

        Note: Yamllint is a linter only and cannot fix issues.
        This method is provided for interface compatibility.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            ToolResult instance indicating that fixing is not supported
        """
        return ToolResult(
            name=self.name,
            success=False,
            output="Yamllint is a linter only and cannot fix issues. Use a YAML formatter like Prettier for formatting.",
            issues_count=0,
        )
