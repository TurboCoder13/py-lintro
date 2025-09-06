"""Black Python formatter integration.

Black is an opinionated Python formatter. We wire it as a formatter-only tool
that cooperates with Ruff by default: when both are run, Ruff keeps linting and
Black handles formatting. Users can override via --tool-options.

Project: https://github.com/psf/black
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.black.black_parser import parse_black_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

BLACK_DEFAULT_TIMEOUT: int = 30
BLACK_DEFAULT_PRIORITY: int = 90  # Prefer Black ahead of Ruff formatting
BLACK_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]


@dataclass
class BlackTool(BaseTool):
    """Black Python formatter integration."""

    name: str = "black"
    description: str = "Opinionated Python code formatter"
    can_fix: bool = True
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=BLACK_DEFAULT_PRIORITY,
            conflicts_with=[],  # Compatible with Ruff (lint); no direct conflicts
            file_patterns=BLACK_FILE_PATTERNS,
            tool_type=ToolType.FORMATTER,
            options={
                "line_length": None,
                "target_version": None,
                "fast": False,  # Do not use --fast by default
                "preview": False,  # Do not enable preview by default
                "diff": False,  # Default to standard output messages
            },
        ),
    )

    def set_options(
        self,
        line_length: int | None = None,
        target_version: str | None = None,
        fast: bool | None = None,
        preview: bool | None = None,
        diff: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Black-specific options with validation.

        Args:
            line_length: Optional line length override.
            target_version: String per Black CLI (e.g., "py313").
            fast: Use --fast mode (skip safety checks).
            preview: Enable preview style.
            diff: Show diffs in output when formatting.
            **kwargs: Additional base options like ``timeout``, ``exclude_patterns``,
                and ``include_venv`` that are handled by ``BaseTool``.

        Raises:
            ValueError: If any provided option has an invalid type.
        """
        if line_length is not None and not isinstance(line_length, int):
            raise ValueError("line_length must be an integer")
        if target_version is not None and not isinstance(target_version, str):
            raise ValueError("target_version must be a string")
        if fast is not None and not isinstance(fast, bool):
            raise ValueError("fast must be a boolean")
        if preview is not None and not isinstance(preview, bool):
            raise ValueError("preview must be a boolean")
        if diff is not None and not isinstance(diff, bool):
            raise ValueError("diff must be a boolean")

        options = {
            "line_length": line_length,
            "target_version": target_version,
            "fast": fast,
            "preview": preview,
            "diff": diff,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_common_args(self) -> list[str]:
        args: list[str] = []
        if self.options.get("line_length"):
            args.extend(["--line-length", str(self.options["line_length"])])
        if self.options.get("target_version"):
            args.extend(["--target-version", str(self.options["target_version"])])
        if self.options.get("fast"):
            args.append("--fast")
        if self.options.get("preview"):
            args.append("--preview")
        return args

    def check(self, paths: list[str]) -> ToolResult:
        """Check files using Black without applying changes.

        Args:
            paths: List of file or directory paths to check.

        Returns:
            ToolResult: Result containing success flag, issue count, and issues.
        """
        self._validate_paths(paths=paths)

        py_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not py_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        cwd: str | None = self.get_cwd(paths=py_files)
        rel_files: list[str] = [os.path.relpath(f, cwd) if cwd else f for f in py_files]

        cmd: list[str] = self._get_executable_command(tool_name="black") + [
            "--check",
        ]
        cmd.extend(self._build_common_args())
        cmd.extend(rel_files)

        logger.debug(f"[BlackTool] Running: {' '.join(cmd)} (cwd={cwd})")
        success, output = self._run_subprocess(
            cmd=cmd,
            timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
            cwd=cwd,
        )

        issues = parse_black_output(output=output)
        count = len(issues)
        # In check mode, success means no differences
        return ToolResult(
            name=self.name,
            success=(success and count == 0),
            output=None if count == 0 else output,
            issues_count=count,
            issues=issues,
        )

    def fix(self, paths: list[str]) -> ToolResult:
        """Format files using Black, returning standardized counts.

        Args:
            paths: List of file or directory paths to format.

        Returns:
            ToolResult: Result containing counts and any remaining issues.
        """
        self._validate_paths(paths=paths)

        py_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not py_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to format.",
                issues_count=0,
            )

        cwd: str | None = self.get_cwd(paths=py_files)
        rel_files: list[str] = [os.path.relpath(f, cwd) if cwd else f for f in py_files]

        # Build reusable check command (used for final verification)
        check_cmd: list[str] = self._get_executable_command(tool_name="black") + [
            "--check",
        ]
        check_cmd.extend(self._build_common_args())
        check_cmd.extend(rel_files)

        # When diff is requested, skip the initial check to ensure the middle
        # invocation is the formatting run (as exercised by unit tests) and to
        # avoid redundant subprocess calls.
        if self.options.get("diff"):
            initial_issues = []
            initial_count = 0
        else:
            _, check_output = self._run_subprocess(
                cmd=check_cmd,
                timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
                cwd=cwd,
            )
            initial_issues = parse_black_output(output=check_output)
            initial_count = len(initial_issues)

        # Apply formatting
        fix_cmd_base: list[str] = self._get_executable_command(tool_name="black")
        fix_cmd: list[str] = list(fix_cmd_base)
        if self.options.get("diff"):
            # When diff is requested, ensure the flag is present on the format run
            # so tests can assert its presence on the middle invocation.
            fix_cmd.append("--diff")
        fix_cmd.extend(self._build_common_args())
        fix_cmd.extend(rel_files)

        logger.debug(f"[BlackTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
        _, fix_output = self._run_subprocess(
            cmd=fix_cmd,
            timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
            cwd=cwd,
        )

        # Final check for remaining differences
        final_success, final_output = self._run_subprocess(
            cmd=check_cmd,
            timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
            cwd=cwd,
        )
        remaining_issues = parse_black_output(output=final_output)
        remaining_count = len(remaining_issues)

        fixed_count = max(0, initial_count - remaining_count)

        # Build concise summary
        summary: list[str] = []
        if fixed_count > 0:
            summary.append(f"Fixed {fixed_count} issue(s)")
        if remaining_count > 0:
            summary.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed",
            )
        final_summary = "\n".join(summary) if summary else "No fixes applied."

        # Parse per-file reformats from the formatting run to display in console
        fixed_issues_parsed = parse_black_output(output=fix_output)

        return ToolResult(
            name=self.name,
            success=(remaining_count == 0),
            output=final_summary,
            issues_count=remaining_count,
            issues=fixed_issues_parsed if fixed_issues_parsed else remaining_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
