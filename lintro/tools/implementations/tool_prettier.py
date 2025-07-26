"""Prettier code formatter integration."""

import os
from dataclasses import dataclass, field

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolConfig, ToolResult
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes


@dataclass
class PrettierTool(BaseTool):
    """Prettier code formatter integration.

    A code formatter that supports multiple languages (JavaScript, TypeScript,
    CSS, HTML, etc.).
    """

    name: str = "prettier"
    description: str = (
        "Code formatter that supports multiple languages (JavaScript, TypeScript, "
        "CSS, HTML, etc.)"
    )
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
        """Try to find the Prettier config file at the project root. Return its
        path or None.

        Returns:
            str | None: Path to config file if found, None otherwise.
        """
        # Assume project root is two levels up from this file
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(root, ".prettierrc.json")
        return config_path if os.path.exists(config_path) else None

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
        import os

        from loguru import logger

        self._validate_paths(paths)
        prettier_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not prettier_files:
            return Tool.to_result(self.name, True, "No files to check.", 0)
        # Use relative paths and set cwd to the common parent
        cwd = self.get_cwd(prettier_files)
        rel_files = [os.path.relpath(f, cwd) if cwd else f for f in prettier_files]
        cmd = ["npx", "prettier", "--check"]
        config_path = self._find_config()
        if config_path:
            cmd.extend(["--config", config_path])
        cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Running: {' '.join(cmd)} (cwd={cwd})")
        _, output = self._run_subprocess(
            cmd, timeout=self.options.get("timeout", self._default_timeout), cwd=cwd
        )
        # Filter out virtual environment files if needed
        if not self.include_venv and output:
            filtered_lines = []
            import re

            venv_pattern = re.compile(
                r"(\.venv|venv|env|ENV|virtualenv|virtual_env|"
                r"virtualenvs|site-packages|node_modules)",
            )
            for line in output.splitlines():
                if not venv_pattern.search(line):
                    filtered_lines.append(line)
            output = "\n".join(filtered_lines)
        issues = parse_prettier_output(output)
        issues_count = len(issues)
        success = issues_count == 0
        if issues_count == 0 and (not output or not output.strip()):
            output = None
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
        import os

        from loguru import logger

        self._validate_paths(paths)
        prettier_files = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not prettier_files:
            return Tool.to_result(self.name, True, "No files to format.", 0)

        # First, check for issues before fixing
        cwd = self.get_cwd(prettier_files)
        rel_files = [os.path.relpath(f, cwd) if cwd else f for f in prettier_files]

        # Check for issues first
        check_cmd = ["npx", "prettier", "--check"]
        config_path = self._find_config()
        if config_path:
            check_cmd.extend(["--config", config_path])
        check_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Checking: {' '.join(check_cmd)} (cwd={cwd})")
        _, check_output = self._run_subprocess(
            check_cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )

        # Parse initial issues
        initial_issues = parse_prettier_output(check_output)
        initial_count = len(initial_issues)

        # Now fix the issues
        fix_cmd = ["npx", "prettier", "--write"]
        if config_path:
            fix_cmd.extend(["--config", config_path])
        fix_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
        _, fix_output = self._run_subprocess(
            fix_cmd, timeout=self.options.get("timeout", self._default_timeout), cwd=cwd
        )

        # Check for remaining issues after fixing
        _, final_check_output = self._run_subprocess(
            check_cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )
        remaining_issues = parse_prettier_output(final_check_output)
        remaining_count = len(remaining_issues)

        # Calculate fixed issues
        fixed_count = initial_count - remaining_count

        # Build output message
        output_lines = []
        if fixed_count > 0:
            output_lines.append(f"Fixed {fixed_count} formatting issue(s)")

        if remaining_count > 0:
            output_lines.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed"
            )
            for issue in remaining_issues[:5]:
                output_lines.append(f"  {issue.file} - {issue.message}")
            if len(remaining_issues) > 5:
                output_lines.append(f"  ... and {len(remaining_issues) - 5} more")

        if initial_count == 0:
            output_lines.append("No formatting issues found")
        elif remaining_count == 0 and fixed_count > 0:
            output_lines.append("All formatting issues were successfully auto-fixed")

        # Add formatting output if available
        if fix_output and fix_output.strip():
            output_lines.append(f"Formatting output:\n{fix_output}")

        final_output = "\n".join(output_lines) if output_lines else "No fixes applied."

        # Success means no remaining issues
        success = remaining_count == 0

        return ToolResult(
            name=self.name,
            success=success,
            output=final_output,
            issues_count=remaining_count,  # Return remaining issues count
        )
