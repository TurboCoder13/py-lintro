"""Actionlint integration for lintro.

This module wires the `actionlint` CLI into Lintro's tool system. It discovers
GitHub Actions workflow files, executes `actionlint`, parses its output into
structured issues, and returns a normalized `ToolResult`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Defaults
ACTIONLINT_DEFAULT_TIMEOUT: int = 30
ACTIONLINT_DEFAULT_PRIORITY: int = 40
ACTIONLINT_FILE_PATTERNS: list[str] = ["*.yml", "*.yaml"]


@dataclass
class ActionlintTool(BaseTool):
    """GitHub Actions workflow linter (actionlint).

    Attributes:
        name: Tool name used across the system.
        description: Human-readable description for listings/help.
        can_fix: Whether the tool can apply fixes (actionlint cannot).
        config: `ToolConfig` with defaults for priority, file patterns, and
            `ToolType` classification.
    """

    name: str = "actionlint"
    description: str = "Static checker for GitHub Actions workflows"
    can_fix: bool = False
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=ACTIONLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=ACTIONLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER | ToolType.INFRASTRUCTURE,
            options={
                "timeout": ACTIONLINT_DEFAULT_TIMEOUT,
                # Option placeholders for future extension (e.g., color, format)
            },
        ),
    )

    def _build_command(self) -> list[str]:
        """Build the base actionlint command.

        We intentionally avoid flags here for maximum portability across
        platforms and actionlint versions. The tool's default text output
        follows the conventional ``file:line:col: message [CODE]`` format,
        which our parser handles directly without requiring a custom format
        switch.

        Returns:
            The base command list for invoking actionlint.
        """
        return ["actionlint"]

    def check(self, paths: list[str]) -> ToolResult:
        """Check GitHub Actions workflow files with actionlint.

        Args:
            paths: File or directory paths to search for workflow files.

        Returns:
            A `ToolResult` containing success status, aggregated output (if any),
            issue count, and parsed issues.
        """
        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        candidate_yaml_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        # Restrict to GitHub Actions workflow location
        workflow_files: list[str] = []
        for file_path in candidate_yaml_files:
            norm = file_path.replace("\\", "/")
            if "/.github/workflows/" in norm:
                workflow_files.append(file_path)
        logger.debug(f"Files to check (actionlint): {workflow_files}")

        if not workflow_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No GitHub workflow files found to check.",
                issues_count=0,
            )

        timeout: int = self.options.get("timeout", ACTIONLINT_DEFAULT_TIMEOUT)
        all_outputs: list[str] = []
        all_issues = []
        all_success = True

        base_cmd = self._build_command()
        for file_path in workflow_files:
            cmd = base_cmd + [file_path]
            try:
                success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
                issues = parse_actionlint_output(output)
                if not success:
                    all_success = False
                if issues:
                    all_outputs.append(output)
                    all_issues.extend(issues)
            except subprocess.TimeoutExpired:
                all_success = False
                all_outputs.append(f"Timeout while checking {file_path}")
            except Exception as e:  # pragma: no cover
                all_success = False
                all_outputs.append(f"Error checking {file_path}: {e}")

        combined_output = "\n".join(all_outputs) if all_outputs else None
        return ToolResult(
            name=self.name,
            success=all_success,
            output=combined_output,
            issues_count=len(all_issues),
            issues=all_issues,
        )

    def fix(self, paths: list[str]) -> ToolResult:
        """Raise since actionlint cannot apply automatic fixes.

        Args:
            paths: File or directory paths (ignored).

        Raises:
            NotImplementedError: Actionlint does not support auto-fixing.
        """
        raise NotImplementedError("actionlint cannot automatically fix issues.")
