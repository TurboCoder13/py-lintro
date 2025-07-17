"""Darglint docstring linter integration."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.models.core.tool import ToolResult
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes
from loguru import logger


@dataclass
class DarglintTool(BaseTool):
    """Darglint docstring linter integration.

    Darglint is a Python docstring linter that checks docstring style and completeness.
    It verifies that docstrings match the function signature and contain all required
    sections.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the core can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "darglint"
    description: str = (
        "Python docstring linter that checks docstring style and completeness"
    )
    can_fix: bool = False  # Darglint can only check, not fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=45,  # Lower priority than formatters, slightly lower than flake8
            conflicts_with=[],  # No direct conflicts
            file_patterns=["*.py"],  # Only applies to Python files
            tool_type=ToolType.LINTER,
            options={
                "timeout": 10,  # Default timeout in seconds per file
                "ignore": None,  # List of error codes to ignore
                "ignore_regex": None,  # Regex pattern for error codes to ignore
                "ignore_syntax": False,  # Whether to ignore syntax errors
                "message_template": None,  # Custom message template
                "verbosity": 1,  # Verbosity level (1-3)
                "strictness": "full",  # Strictness level (short, long, full)
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
        strictness: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Darglint-specific options.

        Args:
            ignore: List of error codes to ignore
            ignore_regex: Regex pattern for error codes to ignore
            ignore_syntax: Whether to ignore syntax errors
            message_template: Custom message template
            verbosity: Verbosity level (1-3)
            strictness: Strictness level (short, long, full)
            **kwargs: Other core options

        Raises:
            ValueError: If an option value is invalid
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
            if not 1 <= verbosity <= 3:
                raise ValueError("verbosity must be between 1 and 3")
        if strictness is not None:
            if not isinstance(strictness, str):
                raise ValueError("strictness must be a string")
            if strictness not in ["short", "long", "full"]:
                raise ValueError("strictness must be one of: short, long, full")

        options = {
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
            List of command arguments
        """
        cmd = ["darglint"]

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

    def _run_darglint(
        self,
        file_path: str,
        timeout: int,
    ) -> tuple[bool, str, int]:
        """Run darglint on a single file.

        Args:
            file_path: Path to the file to check
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output, issues_count)
            - success: True if no issues were found, False otherwise
            - output: Output from darglint
            - issues_count: Number of issues found
        """
        try:
            file_path_obj = Path(file_path)
            cmd = self._build_command() + [str(file_path_obj)]
            logger.debug(f"Running darglint command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            # Darglint outputs findings to stdout
            output = process.stdout
            logger.debug(f"Darglint return code: {process.returncode}")
            logger.debug(f"Darglint output:\n{output}")
            logger.debug(f"Darglint stderr:\n{process.stderr}")

            # Use the parser to count issues
            issues = parse_darglint_output(output)
            issues_count = len(issues)
            logger.debug(f"Parsed {issues_count} issues from output")

            # Darglint returns 0 if no issues, 1 if issues found
            # We consider it a success if no issues were found (exit code 0)
            # We consider it a failure if issues were found (exit code 1)
            success = process.returncode == 0

            return success, output, issues_count
        except subprocess.TimeoutExpired as e:
            return False, f"Timeout after {timeout} seconds: {str(e)}", 1
        except Exception as e:
            return False, f"Error running darglint: {str(e)}", 1

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check Python files for docstring issues with Darglint.

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
        python_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        logger.info(f"Files to check: {python_files}")

        # Process each file with a timeout
        timeout = self.options.get("timeout", 10)
        all_outputs = []
        all_success = True
        skipped_files = []
        processed_files = 0
        total_issues = 0

        for file_path in python_files:
            try:
                # Use _run_darglint to ensure correct parsing and success logic
                success, output, issues_count = self._run_darglint(file_path, timeout)
                if not success:
                    all_success = False
                total_issues += issues_count
                all_outputs.append(output)
                processed_files += 1
            except subprocess.TimeoutExpired:
                skipped_files.append(file_path)
                all_success = False
            except Exception as e:
                all_outputs.append(f"Error processing {file_path}: {str(e)}")
                all_success = False

        # Combine outputs
        output = "\n".join(all_outputs)
        if skipped_files:
            output += f"\n\nSkipped {len(skipped_files)} files due to timeout:"
            for file in skipped_files:
                output += f"\n  - {file}"

        if not output:
            output = "No issues found."

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
            paths: List of file or directory paths to fix

        Raises:
            NotImplementedError: As Darglint does not support fixing issues
        """
        raise NotImplementedError(
            "Darglint cannot automatically fix issues. Run 'lintro check' to see issues."
        )

    def _run_subprocess(
        self,
        cmd: list[str],
        timeout: int,
    ) -> tuple[bool, str]:
        """
        Run a subprocess and handle its output and timeout.

        Args:
            cmd: Command to run
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output)
            - success: True if the command succeeded, False otherwise
            - output: Output from the command
        """
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                return True, stdout or stderr
            else:
                return False, stdout or stderr
        except subprocess.TimeoutExpired:
            process.kill()
            return False, f"Skipped (timeout after {timeout}s)"
