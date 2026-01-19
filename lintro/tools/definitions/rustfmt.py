"""Rustfmt tool definition.

Rustfmt is Rust's official code formatter. It enforces a consistent style
by parsing Rust code and re-printing it with its own rules. It runs via
`cargo fmt` and requires a Cargo.toml file in the project.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.rustfmt.rustfmt_parser import parse_rustfmt_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_positive_int,
)

# Constants for Rustfmt configuration
RUSTFMT_DEFAULT_TIMEOUT: int = 60
RUSTFMT_DEFAULT_PRIORITY: int = 80  # Formatter, runs after linters
RUSTFMT_FILE_PATTERNS: list[str] = ["*.rs"]


def _find_cargo_root(paths: list[str]) -> Path | None:
    """Return the nearest directory containing Cargo.toml for given paths.

    Args:
        paths: List of file paths to search from.

    Returns:
        Path to Cargo.toml directory, or None if not found.
    """
    roots: list[Path] = []
    for raw_path in paths:
        current = Path(raw_path).resolve()
        # If it's a file, start from its parent
        if current.is_file():
            current = current.parent
        # Search upward for Cargo.toml
        for candidate in [current, *list(current.parents)]:
            manifest = candidate / "Cargo.toml"
            if manifest.exists():
                roots.append(candidate)
                break

    if not roots:
        return None

    # Prefer a single root; if multiple, use common path when valid
    unique_roots = set(roots)
    if len(unique_roots) == 1:
        return roots[0]

    try:
        common = Path(os.path.commonpath([str(r) for r in unique_roots]))
    except ValueError:
        return None

    manifest = common / "Cargo.toml"
    return common if manifest.exists() else None


def _build_rustfmt_check_command() -> list[str]:
    """Build the cargo fmt check command.

    Returns:
        List of command arguments.
    """
    return ["cargo", "fmt", "--all", "--", "--check"]


def _build_rustfmt_fix_command() -> list[str]:
    """Build the cargo fmt fix command.

    Returns:
        List of command arguments.
    """
    return ["cargo", "fmt", "--all"]


@register_tool
@dataclass
class RustfmtPlugin(BaseToolPlugin):
    """Rustfmt Rust formatter plugin.

    This plugin integrates Rust's rustfmt formatter with Lintro for formatting
    Rust code consistently.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="rustfmt",
            description="Rust's official code formatter",
            can_fix=True,
            tool_type=ToolType.FORMATTER,
            file_patterns=RUSTFMT_FILE_PATTERNS,
            priority=RUSTFMT_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=["rustfmt.toml", ".rustfmt.toml"],
            version_command=["rustfmt", "--version"],
            min_version="1.0.0",
            default_options={
                "timeout": RUSTFMT_DEFAULT_TIMEOUT,
            },
            default_timeout=RUSTFMT_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Rustfmt-specific options.

        Args:
            timeout: Timeout in seconds (default: 60).
            **kwargs: Additional options.
        """
        validate_positive_int(timeout, "timeout")

        options = filter_none_options(timeout=timeout)
        super().set_options(**options, **kwargs)

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Run `cargo fmt -- --check` and parse formatting issues.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            options,
            no_files_message="No Rust files found to check.",
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        cargo_root = _find_cargo_root(ctx.files)
        if cargo_root is None:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No Cargo.toml found; skipping rustfmt.",
                issues_count=0,
            )

        cmd = _build_rustfmt_check_command()

        try:
            success_cmd, output = self._run_subprocess(
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
            )
        except subprocess.TimeoutExpired:
            timeout_secs = int(ctx.timeout)
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=f"rustfmt execution timed out ({timeout_secs}s limit exceeded).",
                issues_count=1,
                issues=[],
            )

        issues = parse_rustfmt_output(output=output)
        issues_count = len(issues)

        return ToolResult(
            name=self.definition.name,
            success=bool(success_cmd) and issues_count == 0,
            output=None if issues_count == 0 else output,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Run `cargo fmt --all` then re-check for remaining issues.

        Args:
            paths: List of file or directory paths to fix.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with fix results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            options,
            no_files_message="No Rust files found to fix.",
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        cargo_root = _find_cargo_root(ctx.files)
        if cargo_root is None:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No Cargo.toml found; skipping rustfmt.",
                issues_count=0,
                initial_issues_count=0,
                fixed_issues_count=0,
                remaining_issues_count=0,
            )

        check_cmd = _build_rustfmt_check_command()
        timeout_secs = int(ctx.timeout)
        timeout_msg = f"rustfmt execution timed out ({timeout_secs}s limit exceeded)."

        # First, count issues before fixing
        try:
            _, output_check = self._run_subprocess(
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
            )
        except subprocess.TimeoutExpired:
            # Timeout on initial check - can't determine issue counts
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=timeout_msg,
                issues_count=0,
                issues=[],
            )

        initial_issues = parse_rustfmt_output(output=output_check)
        initial_count = len(initial_issues)

        # Run fix
        fix_cmd = _build_rustfmt_fix_command()
        try:
            _, _ = self._run_subprocess(
                cmd=fix_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=timeout_msg,
                issues_count=1,
                issues=initial_issues,
                initial_issues_count=initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )

        # Re-check after fix to count remaining issues
        try:
            _, output_after = self._run_subprocess(
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=timeout_msg,
                issues_count=1,
                issues=initial_issues,
                initial_issues_count=initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )

        remaining_issues = parse_rustfmt_output(output=output_after)
        remaining_count = len(remaining_issues)
        fixed_count = max(0, initial_count - remaining_count)

        return ToolResult(
            name=self.definition.name,
            success=remaining_count == 0,
            output=None,
            issues_count=remaining_count,
            issues=remaining_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
