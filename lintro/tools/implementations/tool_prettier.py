"""Prettier code formatter integration."""

import os
import re
import subprocess
from dataclasses import dataclass, field

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolResult
from lintro.models.core.tool import ToolConfig
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes


@dataclass
class PrettierTool(BaseTool):
    """Prettier code formatter integration.

    A code formatter that supports multiple languages (JavaScript, TypeScript, CSS, HTML, etc.).
    """

    name: str = "prettier"
    description: str = "Code formatter that supports multiple languages (JavaScript, TypeScript, CSS, HTML, etc.)"
    can_fix: bool = True
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=80,  # High priority
            conflicts_with=[],  # No direct conflicts
            file_patterns=[
                "*.js",
                "*.jsx",
                "*.ts",
                "*.tsx",
                "*.css",
                "*.scss",
                "*.less",
                "*.html",
                "*.json",
                "*.yaml",
                "*.yml",
                "*.md",
                "*.graphql",
                "*.vue",
            ],  # Applies to many file types
            tool_type=ToolType.FORMATTER,
        ),
    )

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
    ):
        """
        Set options for the core.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
        """
        self.exclude_patterns = exclude_patterns or []
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout

    def _find_config(self) -> str | None:
        """Try to find the Prettier config file at the project root. Return its path or None.

        Returns:
            str | None: Path to config file if found, None otherwise.
        """
        # Assume project root is two levels up from this file
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(root, ".prettierrc.json")
        return config_path if os.path.exists(config_path) else None

    def _run_prettier(
        self,
        paths: list[str],
        check_only: bool = False,
    ) -> tuple[bool, str, int]:
        """Run Prettier on the given paths.

        Args:
            paths: List of file or directory paths to check/format
            check_only: If True, only check formatting without making changes

        Returns:
            Tuple of (success, output, issues_count)
        """
        cmd = ["npx", "prettier"]
        if check_only:
            cmd.append("--check")
        else:
            cmd.append("--write")
        config_path = self._find_config()
        if config_path:
            cmd.extend(["--config", config_path])
        cmd.extend(paths)

        cwd = self.get_cwd(paths)
        success, output = (
            self._run_subprocess(cmd, timeout=None)
            if cwd is None
            else self._run_subprocess_with_cwd(cmd, cwd)
        )

        # Filter out virtual environment files if needed
        if not self.include_venv and output:
            filtered_lines = []
            venv_pattern = re.compile(
                r"(\.venv|venv|env|ENV|virtualenv|virtual_env|"
                r"virtualenvs|site-packages|node_modules)",
            )
            for line in output.splitlines():
                if not venv_pattern.search(line):
                    filtered_lines.append(line)
            output = "\n".join(filtered_lines)

        # Count issues using the prettier parser
        if check_only:
            # For check mode, parse output to count files that need formatting
            issues = parse_prettier_output(output)
            issues_count = len(issues)
        else:
            # For write mode, count files that were formatted
            issues_count = len(
                [
                    line
                    for line in output.splitlines()
                    if line.strip() and "wrote" in line.lower()
                ]
            )

        # In check mode, having issues means failure
        if check_only and issues_count > 0:
            success = False

        return success, output, issues_count

    def _run_subprocess_with_cwd(
        self,
        cmd: list[str],
        cwd: str,
    ) -> tuple[bool, str]:
        """Run a subprocess command with a specific working directory.

        Args:
            cmd: Command to run as a list of arguments.
            cwd: Working directory to run the command in.

        Returns:
            tuple[bool, str]: Success status and command output.

        Raises:
            CalledProcessError: If command fails with check=True.
            TimeoutExpired: If command exceeds timeout.
            FileNotFoundError: If command executable is not found.
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=self.options.get("timeout", self._default_timeout),
                check=False,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired as e:
            raise subprocess.TimeoutExpired(
                cmd=cmd,
                timeout=self.options.get("timeout", self._default_timeout),
                output=str(e),
            ) from e
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(
                returncode=e.returncode,
                cmd=cmd,
                output=e.output,
                stderr=e.stderr,
            ) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Command not found: {cmd[0]}. Please ensure it is installed and in your PATH."
            ) from e

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Prettier without making changes.

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        prettier_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        success, output, issues_count = self._run_prettier(
            prettier_files, check_only=True
        )
        return Tool.to_result(self.name, success, output, issues_count)

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Format files with Prettier.

        Args:
            paths: List of file or directory paths to format

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        prettier_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        success, output, issues_count = self._run_prettier(
            prettier_files, check_only=False
        )
        return Tool.to_result(self.name, success, output, issues_count)
