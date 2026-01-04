"""Clippy Rust linter integration."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False
from dataclasses import dataclass, field
from pathlib import Path

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.clippy.clippy_parser import parse_clippy_output
from lintro.tools.core.timeout_utils import (
    create_timeout_result,
    get_timeout_value,
    run_subprocess_with_timeout,
)
from lintro.tools.core.tool_base import BaseTool

CLIPPY_DEFAULT_TIMEOUT: int = 120
CLIPPY_DEFAULT_PRIORITY: int = 85
CLIPPY_FILE_PATTERNS: list[str] = ["*.rs", "Cargo.toml"]


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
        for candidate in [current] + list(current.parents):
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


def _build_clippy_command(fix: bool = False) -> list[str]:
    """Build the cargo clippy command.

    Args:
        fix: Whether to include --fix flag.

    Returns:
        List of command arguments.
    """
    cmd = [
        "cargo",
        "clippy",
        "--all-targets",
        "--all-features",
        "--message-format=json",
    ]
    if fix:
        cmd.extend(["--fix", "--allow-dirty", "--allow-staged"])
    return cmd


@dataclass
class ClippyTool(BaseTool):
    """Rust Clippy linter integration.

    Clippy is Rust's official linter with hundreds of lint rules for correctness,
    style, complexity, and performance.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = field(default="clippy")
    description: str = field(
        default="Rust linter for correctness, style, and performance",
    )
    can_fix: bool = field(default=True)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=CLIPPY_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=CLIPPY_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
            options={
                "timeout": CLIPPY_DEFAULT_TIMEOUT,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize base tool settings."""
        super().__post_init__()

    def _verify_tool_version(self) -> ToolResult | None:
        """Verify that Rust toolchain meets minimum version requirements.

        Clippy version is tied to Rust version, so we check rustc version instead.

        Returns:
            Optional[ToolResult]: None if version check passes, or a skip result
                if it fails
        """
        from lintro.tools.core.version_requirements import check_tool_version

        # Check Rust version instead of clippy version
        # rustc --version outputs: "rustc 1.92.0 (ded5c06cf 2025-12-08)"
        # Note: check_tool_version adds --version automatically
        version_info = check_tool_version("clippy", ["rustc"])

        if version_info.version_check_passed:
            return None  # Version check passed

        # Version check failed - return skip result with warning
        skip_message = (
            f"Skipping {self.name}: {version_info.error_message}. "
            f"Minimum required: {version_info.min_version}. "
            f"{version_info.install_hint}"
        )

        return ToolResult(
            name=self.name,
            success=True,  # Not an error, just skipping
            output=skip_message,
            issues_count=0,
        )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Run `cargo clippy` and parse linting issues.

        Args:
            paths: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            no_files_message="No Rust files found to check.",
            default_timeout=CLIPPY_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        cargo_root = _find_cargo_root(ctx.files)
        if cargo_root is None:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Cargo.toml found; skipping clippy.",
                issues_count=0,
            )

        cmd = _build_clippy_command(fix=False)

        try:
            success_cmd, output = run_subprocess_with_timeout(
                tool=self,
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
                tool_name="clippy",
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=ctx.timeout,
                cmd=cmd,
                tool_name="clippy",
            )
            return ToolResult(
                name=self.name,
                success=timeout_result.success,
                output=timeout_result.output,
                issues_count=timeout_result.issues_count,
                issues=timeout_result.issues,
            )

        issues = parse_clippy_output(output=output)
        issues_count = len(issues)

        return ToolResult(
            name=self.name,
            success=bool(success_cmd),
            output=None,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Run `cargo clippy --fix` then re-check for remaining issues.

        Args:
            paths: List of file or directory paths to fix.

        Returns:
            ToolResult: ToolResult instance.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            no_files_message="No Rust files found to fix.",
            default_timeout=CLIPPY_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        cargo_root = _find_cargo_root(ctx.files)
        if cargo_root is None:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Cargo.toml found; skipping clippy.",
                issues_count=0,
                initial_issues_count=0,
                fixed_issues_count=0,
                remaining_issues_count=0,
            )

        check_cmd = _build_clippy_command(fix=False)

        # First, count issues before fixing
        try:
            success_check, output_check = run_subprocess_with_timeout(
                tool=self,
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
                tool_name="clippy",
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=ctx.timeout,
                cmd=check_cmd,
                tool_name="clippy",
            )
            return ToolResult(
                name=self.name,
                success=timeout_result.success,
                output=timeout_result.output,
                issues_count=timeout_result.issues_count,
                issues=timeout_result.issues,
                initial_issues_count=0,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )

        initial_issues = parse_clippy_output(output=output_check)
        initial_count = len(initial_issues)

        # Run fix
        fix_cmd = _build_clippy_command(fix=True)
        try:
            success_fix, output_fix = run_subprocess_with_timeout(
                tool=self,
                cmd=fix_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
                tool_name="clippy",
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=ctx.timeout,
                cmd=fix_cmd,
                tool_name="clippy",
            )
            return ToolResult(
                name=self.name,
                success=timeout_result.success,
                output=timeout_result.output,
                issues_count=timeout_result.issues_count,
                issues=initial_issues,
                initial_issues_count=initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )

        # Re-check after fix to count remaining issues
        try:
            success_after, output_after = run_subprocess_with_timeout(
                tool=self,
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
                tool_name="clippy",
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=ctx.timeout,
                cmd=check_cmd,
                tool_name="clippy",
            )
            return ToolResult(
                name=self.name,
                success=timeout_result.success,
                output=timeout_result.output,
                issues_count=timeout_result.issues_count,
                issues=initial_issues,
                initial_issues_count=initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )

        remaining_issues = parse_clippy_output(output=output_after)
        remaining_count = len(remaining_issues)
        fixed_count = max(0, initial_count - remaining_count)

        return ToolResult(
            name=self.name,
            success=remaining_count == 0,
            output=None,
            issues_count=remaining_count,
            issues=remaining_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
