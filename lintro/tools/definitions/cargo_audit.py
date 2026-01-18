"""Cargo-audit tool definition.

Cargo-audit is a security tool for Rust projects that scans Cargo.lock
for dependencies with known security vulnerabilities from the RustSec
advisory database.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.cargo_audit.cargo_audit_parser import parse_cargo_audit_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool

# Constants for cargo-audit configuration
CARGO_AUDIT_DEFAULT_TIMEOUT: int = 120  # Network operations can be slow
CARGO_AUDIT_DEFAULT_PRIORITY: int = 95  # Security scans run late
CARGO_AUDIT_FILE_PATTERNS: list[str] = ["Cargo.lock"]


def _find_cargo_root(paths: list[str]) -> Path | None:
    """Return the nearest directory containing Cargo.lock for given paths.

    Args:
        paths: List of file paths to search from.

    Returns:
        Path to directory containing Cargo.lock, or None if not found.
    """
    for raw_path in paths:
        current = Path(raw_path).resolve()
        # If it's a file, start from its parent
        if current.is_file():
            current = current.parent
        # Search upward for Cargo.lock
        for candidate in [current, *list(current.parents)]:
            lock_file = candidate / "Cargo.lock"
            if lock_file.exists():
                return candidate

    return None


@register_tool
@dataclass
class CargoAuditPlugin(BaseToolPlugin):
    """Cargo-audit plugin for Lintro.

    Provides security vulnerability scanning for Rust dependencies using
    cargo-audit to check against the RustSec advisory database.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition with cargo-audit configuration.
        """
        return ToolDefinition(
            name="cargo_audit",
            description="Security vulnerability scanner for Rust dependencies",
            can_fix=False,
            tool_type=ToolType.SECURITY,
            file_patterns=CARGO_AUDIT_FILE_PATTERNS,
            priority=CARGO_AUDIT_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".cargo/audit.toml"],
            version_command=["cargo", "audit", "--version"],
            min_version="0.17.0",
            default_options={
                "timeout": CARGO_AUDIT_DEFAULT_TIMEOUT,
            },
            default_timeout=CARGO_AUDIT_DEFAULT_TIMEOUT,
        )

    def set_options(self, **kwargs: Any) -> None:
        """Set tool-specific options.

        Args:
            **kwargs: Options to set, including timeout.

        Raises:
            ValueError: If timeout is negative.
        """
        if "timeout" in kwargs:
            timeout = kwargs["timeout"]
            if isinstance(timeout, int) and timeout < 0:
                raise ValueError("timeout must be non-negative")
        super().set_options(**kwargs)

    def _build_command(self) -> list[str]:
        """Build the cargo-audit command.

        Returns:
            Command list for running cargo-audit with JSON output.
        """
        return ["cargo", "audit", "--json"]

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check Rust dependencies for security vulnerabilities.

        Args:
            paths: List of paths to check.
            options: Additional options for the check.

        Returns:
            ToolResult with security scan results.
        """
        ctx = self._prepare_execution(paths, options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Find Cargo.lock root
        cargo_root = _find_cargo_root(paths)
        if cargo_root is None:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No Cargo.lock found; skipping cargo-audit.",
                issues_count=0,
            )

        cmd = self._build_command()
        try:
            success, output = self._run_subprocess(
                cmd,
                timeout=ctx.timeout,
                cwd=str(cargo_root),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=f"cargo-audit timed out after {ctx.timeout}s",
                issues_count=0,
            )

        issues = parse_cargo_audit_output(output)

        # cargo-audit returns non-zero if vulnerabilities found
        return ToolResult(
            name=self.definition.name,
            success=len(issues) == 0,
            output=output if issues else None,
            issues_count=len(issues),
            issues=issues if issues else None,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Cargo-audit cannot automatically fix vulnerabilities.

        Args:
            paths: List of paths (unused).
            options: Additional options (unused).

        Raises:
            NotImplementedError: Always, as cargo-audit cannot auto-fix.
        """
        raise NotImplementedError(
            "cargo-audit cannot automatically fix vulnerabilities. "
            "Update dependencies manually using `cargo update`.",
        )
