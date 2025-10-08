"""Darglint docstring linter integration."""

import subprocess  # nosec B404 - vetted use via BaseTool._run_subprocess
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.darglint_strictness import (
    DarglintStrictness,
    normalize_darglint_strictness,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for Darglint configuration
DARGLINT_DEFAULT_TIMEOUT: int = 30
DARGLINT_DEFAULT_PRIORITY: int = 45
DARGLINT_FILE_PATTERNS: list[str] = ["*.py"]
DARGLINT_STRICTNESS_LEVELS: tuple[str, ...] = tuple(
    m.name.lower() for m in DarglintStrictness
)
DARGLINT_MIN_VERBOSITY: int = 1
DARGLINT_MAX_VERBOSITY: int = 3
DARGLINT_DEFAULT_VERBOSITY: int = 2
DARGLINT_DEFAULT_STRICTNESS: str = "full"


@dataclass
class DarglintTool(BaseTool):
    """Darglint docstring linter integration.

    Darglint is a Python docstring linter that checks docstring style and completeness.
    It verifies that docstrings match the function signature and contain all required
    sections.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the core can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "darglint"
    description: str = (
        "Python docstring linter that checks docstring style and completeness"
    )
    can_fix: bool = False  # Darglint can only check, not fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=DARGLINT_DEFAULT_PRIORITY,  # Lower priority than formatters, \
            # slightly lower than flake8
            conflicts_with=[],  # No direct conflicts
            file_patterns=DARGLINT_FILE_PATTERNS,  # Only applies to Python files
            tool_type=ToolType.LINTER,
            options={
                "timeout": DARGLINT_DEFAULT_TIMEOUT,  # Default timeout in seconds \
                # per file
                "ignore": None,  # List of error codes to ignore
                "ignore_regex": None,  # Regex pattern for error codes to ignore
                "ignore_syntax": False,  # Whether to ignore syntax errors
                "message_template": None,  # Custom message template
                "verbosity": DARGLINT_DEFAULT_VERBOSITY,  # Verbosity level (1-3) - \
                # use 2 for descriptive messages
                "strictness": DARGLINT_DEFAULT_STRICTNESS,  # Strictness level \
                # (short, long, full)
            },
        ),
    )

    def set_options(
        self,
        ignore: list[str] | None = None,
        ignore_regex: str | None = None,
        ignore_syntax: bool | None = None,
        message_template: str | None = None,
        verbosity: int | None = None,
        strictness: str | DarglintStrictness | None = None,
        **kwargs,
    ) -> None:
        """Set Darglint-specific options.

        Args:
            ignore: list[str] | None: List of error codes to ignore.
            ignore_regex: str | None: Regex pattern for error codes to ignore.
            ignore_syntax: bool | None: Whether to ignore syntax errors.
            message_template: str | None: Custom message template.
            verbosity: int | None: Verbosity level (1-3).
            strictness: str | None: Strictness level (short, long, full).
            **kwargs: Other core options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if ignore is not None and not isinstance(ignore, list):
            raise ValueError("ignore must be a list of error codes")
        if ignore_regex is not None and not isinstance(ignore_regex, str):
            raise ValueError("ignore_regex must be a string")
        if ignore_syntax is not None and not isinstance(ignore_syntax, bool):
            raise ValueError("ignore_syntax must be a boolean")
        if message_template is not None and not isinstance(message_template, str):
            raise ValueError("message_template must be a string")
        if verbosity is not None:
            if not isinstance(verbosity, int):
                raise ValueError("verbosity must be an integer")
            if not DARGLINT_MIN_VERBOSITY <= verbosity <= DARGLINT_MAX_VERBOSITY:
                raise ValueError(
                    f"verbosity must be between {DARGLINT_MIN_VERBOSITY} and "
                    f"{DARGLINT_MAX_VERBOSITY}",
                )
        if strictness is not None:
            strict_enum = normalize_darglint_strictness(  # type: ignore[arg-type]
                strictness,
            )
            strictness = strict_enum.name.lower()

        options: dict = {
            "ignore": ignore,
            "ignore_regex": ignore_regex,
            "ignore_syntax": ignore_syntax,
            "message_template": message_template,
            "verbosity": verbosity,
            "strictness": strictness,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the Darglint command.

        Returns:
            list[str]: List of command arguments.
        """
        # Prefer running via the active environment (uv run) if available,
        # falling back to a direct executable when necessary.
        cmd: list[str] = self._get_executable_command("darglint")

        # Add configuration options
        if self.options.get("ignore"):
            cmd.extend(["--ignore", ",".join(self.options["ignore"])])
        if self.options.get("ignore_regex"):
            cmd.extend(["--ignore-regex", self.options["ignore_regex"]])
        if self.options.get("ignore_syntax"):
            cmd.append("--ignore-syntax")
        # Remove message_template override to use default output
        # if self.options.get("message_template"):
        #     cmd.extend(["--message-template", self.options["message_template"]])
        if self.options.get("verbosity"):
            cmd.extend(["--verbosity", str(self.options["verbosity"])])
        if self.options.get("strictness"):
            cmd.extend(["--strictness", self.options["strictness"]])

        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check Python files for docstring issues with Darglint.

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )
        # Use shared utility for file discovery
        python_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        logger.debug(f"Files to check: {python_files}")

        timeout: int = self.options.get("timeout", DARGLINT_DEFAULT_TIMEOUT)
        all_outputs: list[str] = []
        all_success: bool = True
        skipped_files: list[str] = []
        total_issues: int = 0

        for file_path in python_files:
            cmd: list[str] = self._build_command() + [str(file_path)]
            try:
                success: bool
                output: str
                success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
                issues = parse_darglint_output(output=output)
                issues_count: int = len(issues)
                if not (success and issues_count == 0):
                    all_success = False
                total_issues += issues_count
                # Store parsed issues on the aggregate result later via ToolResult
                all_outputs.append(output)
            except subprocess.TimeoutExpired:
                skipped_files.append(file_path)
                all_success = False
            except Exception as e:
                all_outputs.append(f"Error processing {file_path}: {str(e)}")
                all_success = False

        output: str = "\n".join(all_outputs)
        if skipped_files:
            output += f"\n\nSkipped {len(skipped_files)} files due to timeout:"
            for file in skipped_files:
                output += f"\n  - {file}"

        if not output:
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
        """Darglint cannot fix issues, only report them.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Raises:
            NotImplementedError: As Darglint does not support fixing issues.
        """
        raise NotImplementedError(
            "Darglint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
