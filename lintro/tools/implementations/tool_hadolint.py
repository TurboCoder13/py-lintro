"""Hadolint Dockerfile linter integration."""

import subprocess
from dataclasses import dataclass, field
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes
from loguru import logger


@dataclass
class HadolintTool(BaseTool):
    """Hadolint Dockerfile linter integration.

    Hadolint is a Dockerfile linter that helps you build best practice Docker images.
    It parses the Dockerfile into an AST and performs rules on top of the AST.
    It also uses ShellCheck to lint the Bash code inside RUN instructions.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues (hadolint cannot fix issues)
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "hadolint"
    description: str = (
        "Dockerfile linter that helps you build best practice Docker images"
    )
    can_fix: bool = False  # Hadolint can only check, not fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=50,  # Medium priority for infrastructure linting
            conflicts_with=[],  # No direct conflicts
            file_patterns=["Dockerfile", "Dockerfile.*", "*.dockerfile"],
            tool_type=ToolType.LINTER | ToolType.INFRASTRUCTURE,
            options={
                "timeout": 30,  # Default timeout in seconds
                "format": "tty",  # Output format (tty, json, checkstyle, etc.)
                "failure_threshold": "info",  # Threshold for failure (error, warning, info, style)
                "ignore": None,  # List of rule codes to ignore
                "trusted_registries": None,  # List of trusted Docker registries
                "require_labels": None,  # List of required labels with schemas
                "strict_labels": False,  # Whether to use strict label checking
                "no_fail": False,  # Whether to suppress exit codes
                "no_color": True,  # Disable color output for parsing
            },
        ),
    )

    def set_options(
        self,
        format: str | None = None,
        failure_threshold: str | None = None,
        ignore: list[str] | None = None,
        trusted_registries: list[str] | None = None,
        require_labels: list[str] | None = None,
        strict_labels: bool | None = None,
        no_fail: bool | None = None,
        no_color: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Hadolint-specific options.

        Args:
            format: Output format (tty, json, checkstyle, codeclimate, etc.)
            failure_threshold: Exit with failure only when rules with severity >= threshold
            ignore: List of rule codes to ignore (e.g., ['DL3006', 'SC2086'])
            trusted_registries: List of trusted Docker registries
            require_labels: List of required labels with schemas (e.g., ['version:semver'])
            strict_labels: Whether to use strict label checking
            no_fail: Whether to suppress exit codes
            no_color: Whether to disable color output
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if format is not None and format not in [
            "tty",
            "json",
            "checkstyle",
            "codeclimate",
            "gitlab_codeclimate",
            "gnu",
            "codacy",
            "sonarqube",
            "sarif",
        ]:
            raise ValueError(
                f"Invalid format '{format}'. Must be one of: tty, json, checkstyle, "
                "codeclimate, gitlab_codeclimate, gnu, codacy, sonarqube, sarif"
            )

        if failure_threshold is not None and failure_threshold not in [
            "error",
            "warning",
            "info",
            "style",
            "ignore",
            "none",
        ]:
            raise ValueError(
                f"Invalid failure_threshold '{failure_threshold}'. Must be one of: "
                "error, warning, info, style, ignore, none"
            )

        if ignore is not None and not isinstance(ignore, list):
            raise ValueError("ignore must be a list of rule codes")

        if trusted_registries is not None and not isinstance(trusted_registries, list):
            raise ValueError("trusted_registries must be a list of registry URLs")

        if require_labels is not None and not isinstance(require_labels, list):
            raise ValueError("require_labels must be a list of label schemas")

        if strict_labels is not None and not isinstance(strict_labels, bool):
            raise ValueError("strict_labels must be a boolean")

        if no_fail is not None and not isinstance(no_fail, bool):
            raise ValueError("no_fail must be a boolean")

        if no_color is not None and not isinstance(no_color, bool):
            raise ValueError("no_color must be a boolean")

        options = {
            "format": format,
            "failure_threshold": failure_threshold,
            "ignore": ignore,
            "trusted_registries": trusted_registries,
            "require_labels": require_labels,
            "strict_labels": strict_labels,
            "no_fail": no_fail,
            "no_color": no_color,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the hadolint command.

        Returns:
            List of command arguments
        """
        cmd = ["hadolint"]

        # Add format option
        format_option = self.options.get("format", "tty")
        cmd.extend(["--format", format_option])

        # Add failure threshold
        failure_threshold = self.options.get("failure_threshold", "info")
        cmd.extend(["--failure-threshold", failure_threshold])

        # Add ignore rules
        ignore_rules = self.options.get("ignore", [])
        for rule in ignore_rules:
            cmd.extend(["--ignore", rule])

        # Add trusted registries
        trusted_registries = self.options.get("trusted_registries", [])
        for registry in trusted_registries:
            cmd.extend(["--trusted-registry", registry])

        # Add required labels
        require_labels = self.options.get("require_labels", [])
        for label in require_labels:
            cmd.extend(["--require-label", label])

        # Add strict labels
        if self.options.get("strict_labels", False):
            cmd.append("--strict-labels")

        # Add no-fail option
        if self.options.get("no_fail", False):
            cmd.append("--no-fail")

        # Add no-color option (default to True for better parsing)
        if self.options.get("no_color", True):
            cmd.append("--no-color")

        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Hadolint.

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
        dockerfile_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        logger.debug(f"Files to check: {dockerfile_files}")

        timeout = self.options.get("timeout", 30)
        all_outputs = []
        all_success = True
        skipped_files = []
        total_issues = 0

        for file_path in dockerfile_files:
            cmd = self._build_command() + [str(file_path)]
            try:
                success, output = self._run_subprocess(cmd, timeout=timeout)
                issues = parse_hadolint_output(output)
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
        """Hadolint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Raises:
            NotImplementedError: As Hadolint does not support fixing issues
        """
        raise NotImplementedError(
            "Hadolint cannot automatically fix issues. Run 'lintro check' to see issues."
        )
