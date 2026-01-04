"""Hadolint Dockerfile linter integration."""

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

import click

from lintro.enums.hadolint_enums import (
    HadolintFailureThreshold,
    HadolintFormat,
    normalize_hadolint_format,
    normalize_hadolint_threshold,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
from lintro.tools.core.tool_base import BaseTool

# Constants for Hadolint configuration
HADOLINT_DEFAULT_TIMEOUT: int = 30
HADOLINT_DEFAULT_PRIORITY: int = 50
HADOLINT_FILE_PATTERNS: list[str] = ["Dockerfile", "Dockerfile.*"]
HADOLINT_DEFAULT_FORMAT: str = "tty"
HADOLINT_DEFAULT_FAILURE_THRESHOLD: str = "info"
HADOLINT_DEFAULT_NO_COLOR: bool = True
HADOLINT_FORMATS: tuple[str, ...] = tuple(m.name.lower() for m in HadolintFormat)
HADOLINT_FAILURE_THRESHOLDS: tuple[str, ...] = tuple(
    m.name.lower() for m in HadolintFailureThreshold
)


@dataclass
class HadolintTool(BaseTool):
    """Hadolint Dockerfile linter integration.

    Hadolint is a Dockerfile linter that helps you build best practice Docker images.
    It parses the Dockerfile into an AST and performs rules on top of the AST.
    It also uses ShellCheck to lint the Bash code inside RUN instructions.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues (hadolint cannot fix issues).
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "hadolint"
    description: str = (
        "Dockerfile linter that helps you build best practice Docker images"
    )
    can_fix: bool = field(default=False)  # Hadolint can only check, not fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=HADOLINT_DEFAULT_PRIORITY,  # Medium priority for \
            # infrastructure linting
            conflicts_with=[],  # No direct conflicts
            file_patterns=HADOLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER | ToolType.INFRASTRUCTURE,
            options={
                "timeout": HADOLINT_DEFAULT_TIMEOUT,  # Default timeout in seconds
                "format": HADOLINT_DEFAULT_FORMAT,  # Output format (tty, json, \
                # checkstyle, etc.)
                "failure_threshold": HADOLINT_DEFAULT_FAILURE_THRESHOLD,  # \
                # Threshold for failure (error, warning, info, style)
                "ignore": None,  # List of rule codes to ignore
                "trusted_registries": None,  # List of trusted Docker registries
                "require_labels": None,  # List of required labels with schemas
                "strict_labels": False,  # Whether to use strict label checking
                "no_fail": False,  # Whether to suppress exit codes
                "no_color": HADOLINT_DEFAULT_NO_COLOR,  # Disable color output \
                # for parsing
            },
        ),
    )

    def set_options(
        self,
        format: str | HadolintFormat | None = None,
        failure_threshold: str | HadolintFailureThreshold | None = None,
        ignore: list[str] | None = None,
        trusted_registries: list[str] | None = None,
        require_labels: list[str] | None = None,
        strict_labels: bool | None = None,
        no_fail: bool | None = None,
        no_color: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Hadolint-specific options.

        Args:
            format: str | None: Output format (tty, json, checkstyle, codeclimate, \
                etc.).
            failure_threshold: str | None: Exit with failure only when rules with \
                severity >= threshold.
            ignore: list[str] | None: List of rule codes to ignore (e.g., \
                ['DL3006', 'SC2086']).
            trusted_registries: list[str] | None: List of trusted Docker registries.
            require_labels: list[str] | None: List of required labels with schemas \
                (e.g., ['version:semver']).
            strict_labels: bool | None: Whether to use strict label checking.
            no_fail: bool | None: Whether to suppress exit codes.
            no_color: bool | None: Whether to disable color output.
            **kwargs: Other tool options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if format is not None:
            fmt_enum = normalize_hadolint_format(format)  # type: ignore[arg-type]
            format = fmt_enum.name.lower()

        if failure_threshold is not None:
            thr_enum = normalize_hadolint_threshold(  # type: ignore[arg-type]
                failure_threshold,
            )
            failure_threshold = thr_enum.name.lower()

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

        options: dict = {
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
            list[str]: List of command arguments.
        """
        cmd: list[str] = ["hadolint"]

        # Add format option
        format_option: str = self.options.get("format", HADOLINT_DEFAULT_FORMAT)
        cmd.extend(["--format", format_option])

        # Add failure threshold
        failure_threshold: str = self.options.get(
            "failure_threshold",
            HADOLINT_DEFAULT_FAILURE_THRESHOLD,
        )
        cmd.extend(["--failure-threshold", failure_threshold])

        # Add ignore rules
        ignore_rules: list[str] | None = self.options.get("ignore")
        if ignore_rules is None:
            ignore_rules = []
        for rule in ignore_rules:
            cmd.extend(["--ignore", rule])

        # Add trusted registries
        trusted_registries: list[str] | None = self.options.get("trusted_registries")
        if trusted_registries is None:
            trusted_registries = []
        for registry in trusted_registries:
            cmd.extend(["--trusted-registry", registry])

        # Add required labels
        require_labels: list[str] | None = self.options.get("require_labels")
        if require_labels is None:
            require_labels = []
        for label in require_labels:
            cmd.extend(["--require-label", label])

        # Add strict labels
        if self.options.get("strict_labels", False):
            cmd.append("--strict-labels")

        # Add no-fail option
        if self.options.get("no_fail", False):
            cmd.append("--no-fail")

        # Add no-color option (default to True for better parsing)
        if self.options.get("no_color", HADOLINT_DEFAULT_NO_COLOR):
            cmd.append("--no-color")

        return cmd

    def _process_single_file(
        self,
        file_path: str,
        timeout: int,
        results: dict,
    ) -> None:
        """Process a single Dockerfile with hadolint.

        Args:
            file_path: Path to the Dockerfile.
            timeout: Timeout in seconds.
            results: Mutable dict to accumulate results.
        """
        cmd: list[str] = self._build_command() + [str(file_path)]
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_hadolint_output(output=output)
            issues_count = len(issues)

            if not success:
                results["all_success"] = False
            results["total_issues"] += issues_count

            if not success or issues:
                results["all_outputs"].append(output)
            if issues:
                results["all_issues"].extend(issues)
        except subprocess.TimeoutExpired:
            results["skipped_files"].append(file_path)
            results["all_success"] = False
            results["execution_failures"] += 1
        except Exception as e:
            results["all_outputs"].append(f"Error processing {file_path}: {str(e)}")
            results["all_success"] = False
            results["execution_failures"] += 1

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Hadolint.

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            default_timeout=HADOLINT_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Hadolint processes files one at a time (doesn't support batch mode)
        # Use files directly since hadolint needs absolute paths
        dockerfile_files = ctx.files

        # Accumulate results across all files
        results: dict = {
            "all_outputs": [],
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "execution_failures": 0,
            "total_issues": 0,
        }

        # Show progress bar only when processing multiple files
        if len(dockerfile_files) >= 2:
            with click.progressbar(
                dockerfile_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file(file_path, ctx.timeout, results)
        else:
            for file_path in dockerfile_files:
                self._process_single_file(file_path, ctx.timeout, results)

        # Build output from accumulated results
        output: str = (
            "\n".join(results["all_outputs"]) if results["all_outputs"] else ""
        )
        if results["execution_failures"] > 0:
            if output:
                output += "\n\n"
            if results["skipped_files"]:
                output += (
                    f"Skipped/failed {results['execution_failures']} file(s) due to "
                    f"execution failures (including timeouts)"
                )
                output += f" (timeout: {ctx.timeout}s):"
                for file in results["skipped_files"]:
                    output += f"\n  - {file}"
            else:
                output += (
                    f"Failed to process {results['execution_failures']} file(s) "
                    "due to execution errors"
                )

        if not output.strip():
            output = None

        return ToolResult(
            name=self.name,
            success=results["all_success"],
            output=output,
            issues_count=results["total_issues"],
            issues=results["all_issues"],
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Hadolint cannot fix issues, only report them.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Raises:
            NotImplementedError: As Hadolint does not support fixing issues.
        """
        raise NotImplementedError(
            "Hadolint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
