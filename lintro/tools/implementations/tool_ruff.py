"""Ruff Python linter and formatter integration."""

import subprocess
from dataclasses import dataclass, field
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig
from lintro.models.core.tool import ToolResult
from lintro.parsers.ruff.ruff_parser import parse_ruff_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes
from loguru import logger


@dataclass
class RuffTool(BaseTool):
    """Ruff Python linter and formatter integration.

    Ruff is an extremely fast Python linter and code formatter written in Rust.
    It can replace multiple Python tools like flake8, black, isort, and more.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "ruff"
    description: str = (
        "Extremely fast Python linter and formatter that replaces multiple tools"
    )
    can_fix: bool = True  # Ruff can both check and fix issues
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=85,  # High priority, higher than most linters
            conflicts_with=[],  # Can work alongside other tools
            file_patterns=["*.py", "*.pyi"],  # Python files only
            tool_type=ToolType.LINTER | ToolType.FORMATTER,  # Both linter and formatter
            options={
                "timeout": 30,  # Default timeout in seconds
                "select": None,  # Rules to enable
                "ignore": None,  # Rules to ignore
                "extend_select": None,  # Additional rules to enable
                "extend_ignore": None,  # Additional rules to ignore
                "line_length": None,  # Line length limit
                "target_version": None,  # Python version target
                "fix_only": False,  # Only apply fixes, don't report remaining issues
                "unsafe_fixes": True,  # Include unsafe fixes by default for fmt command
                "show_fixes": False,  # Show enumeration of fixes applied
                "format": True,  # Whether to run formatter as well
            },
        ),
    )

    def set_options(
        self,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        extend_select: list[str] | None = None,
        extend_ignore: list[str] | None = None,
        line_length: int | None = None,
        target_version: str | None = None,
        fix_only: bool | None = None,
        unsafe_fixes: bool | None = None,
        show_fixes: bool | None = None,
        format: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Ruff-specific options.

        Args:
            select: Rules to enable
            ignore: Rules to ignore
            extend_select: Additional rules to enable
            extend_ignore: Additional rules to ignore
            line_length: Line length limit
            target_version: Python version target
            fix_only: Only apply fixes, don't report remaining issues
            unsafe_fixes: Include unsafe fixes
            show_fixes: Show enumeration of fixes applied
            format: Whether to run formatter as well
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if select is not None and not isinstance(select, list):
            raise ValueError("select must be a list of rule codes")
        if ignore is not None and not isinstance(ignore, list):
            raise ValueError("ignore must be a list of rule codes")
        if extend_select is not None and not isinstance(extend_select, list):
            raise ValueError("extend_select must be a list of rule codes")
        if extend_ignore is not None and not isinstance(extend_ignore, list):
            raise ValueError("extend_ignore must be a list of rule codes")
        if line_length is not None:
            if not isinstance(line_length, int):
                raise ValueError("line_length must be an integer")
            if line_length <= 0:
                raise ValueError("line_length must be positive")
        if target_version is not None and not isinstance(target_version, str):
            raise ValueError("target_version must be a string")
        if fix_only is not None and not isinstance(fix_only, bool):
            raise ValueError("fix_only must be a boolean")
        if unsafe_fixes is not None and not isinstance(unsafe_fixes, bool):
            raise ValueError("unsafe_fixes must be a boolean")
        if show_fixes is not None and not isinstance(show_fixes, bool):
            raise ValueError("show_fixes must be a boolean")
        if format is not None and not isinstance(format, bool):
            raise ValueError("format must be a boolean")

        options = {
            "select": select,
            "ignore": ignore,
            "extend_select": extend_select,
            "extend_ignore": extend_ignore,
            "line_length": line_length,
            "target_version": target_version,
            "fix_only": fix_only,
            "unsafe_fixes": unsafe_fixes,
            "show_fixes": show_fixes,
            "format": format,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_check_command(
        self,
        files: list[str],
        fix: bool = False,
    ) -> list[str]:
        """Build the ruff check command.

        Args:
            files: List of files to check
            fix: Whether to apply fixes

        Returns:
            List of command arguments
        """
        cmd = self._get_executable_command("ruff") + ["check"]

        # Add configuration options
        if self.options.get("select"):
            cmd.extend(["--select", ",".join(self.options["select"])])
        if self.options.get("ignore"):
            cmd.extend(["--ignore", ",".join(self.options["ignore"])])
        if self.options.get("extend_select"):
            cmd.extend(["--extend-select", ",".join(self.options["extend_select"])])
        if self.options.get("extend_ignore"):
            cmd.extend(["--extend-ignore", ",".join(self.options["extend_ignore"])])
        if self.options.get("line_length"):
            cmd.extend(["--line-length", str(self.options["line_length"])])
        if self.options.get("target_version"):
            cmd.extend(["--target-version", self.options["target_version"]])

        # Fix options
        if fix:
            cmd.append("--fix")
            if self.options.get("unsafe_fixes"):
                cmd.append("--unsafe-fixes")
            if self.options.get("show_fixes"):
                cmd.append("--show-fixes")
            if self.options.get("fix_only"):
                cmd.append("--fix-only")

        # Output format
        cmd.extend(["--output-format", "json"])

        # Add files
        cmd.extend(files)

        return cmd

    def _build_format_command(
        self,
        files: list[str],
        check_only: bool = False,
    ) -> list[str]:
        """Build the ruff format command.

        Args:
            files: List of files to format
            check_only: Whether to only check formatting without applying changes

        Returns:
            List of command arguments
        """
        cmd = self._get_executable_command("ruff") + ["format"]

        if check_only:
            cmd.append("--check")

        # Add configuration options
        if self.options.get("line_length"):
            cmd.extend(["--line-length", str(self.options["line_length"])])
        if self.options.get("target_version"):
            cmd.extend(["--target-version", self.options["target_version"]])

        # Add files
        cmd.extend(files)

        return cmd

    def _run_ruff_command(
        self,
        cmd: list[str],
        timeout: int,
    ) -> tuple[bool, str, str, int]:
        """Run a ruff command and parse the results.

        Args:
            cmd: Command to run
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr, issues_count)
            - success: True if no issues were found or successfully fixed
            - stdout: Standard output from ruff
            - stderr: Standard error from ruff
            - issues_count: Number of issues found or fixed
        """
        try:
            logger.debug(f"Running ruff command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            logger.debug(f"Ruff return code: {result.returncode}")
            logger.debug(f"Ruff stdout:\n{result.stdout}")
            logger.debug(f"Ruff stderr:\n{result.stderr}")

            # Parse issues if it's a check command with JSON output
            issues_count = 0
            if "--output-format" in cmd and "json" in cmd:
                issues = parse_ruff_output(result.stdout)
                issues_count = len(issues)

            # For ruff check: 0 = no issues, 1 = issues found
            # For ruff format: 0 = no changes needed, 1 = changes needed/made
            success = result.returncode == 0

            return success, result.stdout, result.stderr, issues_count

        except subprocess.TimeoutExpired as e:
            return False, "", f"Timeout after {timeout} seconds: {str(e)}", 1
        except Exception as e:
            return False, "", f"Error running ruff: {str(e)}", 1

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Ruff.

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

        if not python_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Python files found to check.",
                issues_count=0,
            )

        logger.info(f"Files to check: {python_files}")

        # Build and run check command
        timeout = self.options.get("timeout", 30)
        cmd = self._build_check_command(python_files, fix=False)
        success, stdout, stderr, issues_count = self._run_ruff_command(cmd, timeout)

        # Combine stdout and stderr for output
        output = stdout
        if stderr:
            output += "\n" + stderr

        # Format output for display
        if not output or output.strip() == "[]":
            output = "No issues found."

        return ToolResult(
            name=self.name,
            success=success,
            output=output,
            issues_count=issues_count,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files with Ruff.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to fix.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not python_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Python files found to fix.",
                issues_count=0,
            )

        logger.info(f"Files to fix: {python_files}")
        timeout = self.options.get("timeout", 30)
        all_outputs = []
        total_issues = 0
        overall_success = True

        # Run ruff check --fix
        cmd = self._build_check_command(python_files, fix=True)
        success, stdout, stderr, issues_count = self._run_ruff_command(cmd, timeout)

        # Handle output properly - ruff check --fix returns JSON or error messages
        if stdout and stdout.strip() != "[]":
            if stdout.strip().startswith("["):
                # JSON output - parse and format nicely
                try:
                    import json

                    issues = json.loads(stdout)
                    issues_count = len(issues)
                    total_issues += issues_count

                    if issues:
                        # These are issues that could NOT be auto-fixed
                        all_outputs.append(
                            f"Found {len(issues)} issue(s) that cannot be auto-fixed"
                        )
                        # Include details about the unfixable issues
                        for issue in issues[:5]:  # Show first 5 issues
                            file_path = issue.get("filename", "")
                            # Try to make path relative to current working directory
                            import os

                            try:
                                file_rel = os.path.relpath(file_path)
                            except (ValueError, TypeError):
                                file_rel = file_path
                            all_outputs.append(
                                f"  {file_rel}:{issue.get('location', {}).get('row', '?')} - {issue.get('message', 'Unknown issue')}"
                            )
                        if len(issues) > 5:
                            all_outputs.append(f"  ... and {len(issues) - 5} more")
                    else:
                        all_outputs.append(
                            "All linting issues were successfully auto-fixed"
                        )
                except json.JSONDecodeError:
                    all_outputs.append(f"Linting fixes:\n{stdout}")
            else:
                # Text output (error messages, etc.)
                all_outputs.append(f"Linting fixes:\n{stdout}")
        else:
            # Empty JSON output means all issues were fixed successfully
            # Check if there was any stderr output that indicates fixes were applied
            if stderr and stderr.strip():
                all_outputs.append(f"Linting fixes:\n{stderr.strip()}")
            else:
                all_outputs.append("All linting issues were successfully auto-fixed")

        # For fix command, if issues remain unfixed, it's a partial success
        if not success and issues_count > 0:
            # Command failed because issues remain, but this is expected for unfixable issues
            overall_success = (
                False  # We'll keep this as false to indicate issues remain
            )

        # Run ruff format if enabled
        if self.options.get("format", True):
            format_cmd = self._build_format_command(python_files, check_only=False)
            format_success, format_stdout, format_stderr, _ = self._run_ruff_command(
                format_cmd, timeout
            )

            # Combine stdout and stderr for formatting output
            format_output = format_stdout
            if format_stderr:
                format_output += "\n" + format_stderr

            if format_output and format_output.strip():
                all_outputs.append(f"Formatting:\n{format_output}")
            else:
                all_outputs.append("No formatting changes needed")

            if not format_success:
                overall_success = False

        # Combine outputs
        final_output = "\n\n".join(all_outputs) if all_outputs else "No fixes applied."

        return ToolResult(
            name=self.name,
            success=overall_success,
            output=final_output,
            issues_count=total_issues,
        )
