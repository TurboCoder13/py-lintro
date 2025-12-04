"""Markdownlint-cli2 Markdown linter integration."""

import json
import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.utils.unified_config import _strip_jsonc_comments
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.markdownlint.markdownlint_parser import parse_markdownlint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.config import get_central_line_length
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants
MARKDOWNLINT_DEFAULT_TIMEOUT: int = 30
MARKDOWNLINT_DEFAULT_PRIORITY: int = 45
MARKDOWNLINT_FILE_PATTERNS: list[str] = [
    "*.md",
    "*.markdown",
]


@dataclass
class MarkdownlintTool(BaseTool):
    """Markdownlint-cli2 Markdown linter integration.

    Markdownlint-cli2 is a linter for Markdown files that checks for style
    issues and best practices.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "markdownlint"
    description: str = "Markdown linter for style checking and best practices"
    can_fix: bool = False
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=MARKDOWNLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=MARKDOWNLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
            options={
                "timeout": MARKDOWNLINT_DEFAULT_TIMEOUT,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool."""
        super().__post_init__()

    def _verify_tool_version(self) -> ToolResult | None:
        """Verify that markdownlint-cli2 meets minimum version requirements.

        Overrides base implementation to use the correct executable name.

        Returns:
            Optional[ToolResult]: None if version check passes, or a skip result
                if it fails
        """
        from lintro.tools.core.version_requirements import check_tool_version

        # Use the correct command for markdownlint-cli2
        command = self._get_markdownlint_command()
        version_info = check_tool_version(self.name, command)

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

    def set_options(
        self,
        timeout: int | None = None,
        line_length: int | None = None,
        **kwargs,
    ) -> None:
        """Set Markdownlint-specific options.

        Args:
            timeout: Timeout in seconds per file (default: 30)
            line_length: Line length for MD013 rule. If not provided, uses
                central line_length from [tool.lintro] or falls back to Ruff's
                line-length setting.
            **kwargs: Other tool options

        Raises:
            ValueError: If timeout is not an integer or is not positive, or
                if line_length is not an integer or is not positive
        """
        if timeout is not None:
            if not isinstance(timeout, int):
                raise ValueError("timeout must be an integer")
            if timeout <= 0:
                raise ValueError("timeout must be positive")

        # Use provided line_length, or get from central config
        if line_length is None:
            line_length = get_central_line_length()

        if line_length is not None:
            if not isinstance(line_length, int):
                raise ValueError("line_length must be an integer")
            if line_length <= 0:
                raise ValueError("line_length must be positive")
            # Store for use in check() method
            self.options["line_length"] = line_length

        super().set_options(timeout=timeout, **kwargs)

    def _get_markdownlint_command(self) -> list[str]:
        """Get the command to run markdownlint-cli2.

        Returns:
            list[str]: Command arguments for markdownlint-cli2.
        """
        import shutil

        # Use npx to run markdownlint-cli2 (similar to prettier)
        if shutil.which("npx"):
            return ["npx", "--yes", "markdownlint-cli2"]
        # Fallback to direct executable if npx not found
        return ["markdownlint-cli2"]

    def _ensure_markdownlint_config(
        self,
        cwd: str | None,
        line_length: int,
    ) -> None:
        """Ensure markdownlint-cli2 config file has the correct line length.

        Creates or updates .markdownlint-cli2.jsonc in the working directory with
        MD013 rule configured to use the central line_length setting.

        Args:
            cwd: Working directory where config should be created/updated
            line_length: Line length to configure for MD013 rule
        """
        if not cwd:
            return

        # markdownlint-cli2 uses .markdownlint-cli2.jsonc format
        config_path = Path(cwd) / ".markdownlint-cli2.jsonc"
        config_wrapper: dict[str, object] = {}

        # Load existing config if it exists
        if config_path.exists():
            try:
                with config_path.open(encoding="utf-8") as f:
                    content = f.read()
                    # Strip JSONC comments safely (preserves strings)
                    content = _strip_jsonc_comments(content)
                    config_wrapper = json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logger.debug(
                    f"[MarkdownlintTool] Could not read existing config: {e}",
                )
                config_wrapper = {}

        # markdownlint-cli2 wraps config in a "config" key
        if "config" not in config_wrapper:
            config_wrapper["config"] = {}
        config = config_wrapper["config"]

        # Ensure config is a dict
        if not isinstance(config, dict):
            config = {}
            config_wrapper["config"] = config

        # Update MD013 rule with line_length
        # Ignore code blocks and tables as they often have long lines
        if "MD013" not in config:
            config["MD013"] = {}
        if not isinstance(config["MD013"], dict):
            config["MD013"] = {}
        config["MD013"]["line_length"] = line_length
        config["MD013"]["code_blocks"] = False
        config["MD013"]["tables"] = False

        # Write config file as JSONC (JSON with comments)
        try:
            with config_path.open("w", encoding="utf-8") as f:
                # Write as JSON (markdownlint-cli2 accepts JSON in .jsonc files)
                json.dump(config_wrapper, f, indent=2)
            logger.debug(
                f"[MarkdownlintTool] Updated {config_path} "
                f"with line_length={line_length}",
            )
        except (PermissionError, OSError) as e:
            logger.warning(
                f"[MarkdownlintTool] Could not write config file {config_path}: {e}",
            )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Markdownlint.

        Args:
            paths: List of file or directory paths to check.

        Returns:
            ToolResult: Result of the check operation.
        """
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        markdown_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        logger.debug(
            f"[MarkdownlintTool] Discovered {len(markdown_files)} files matching "
            f"patterns: {self.config.file_patterns}",
        )
        logger.debug(
            f"[MarkdownlintTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if markdown_files:
            logger.debug(
                f"[MarkdownlintTool] Files to check (first 10): "
                f"{markdown_files[:10]}",
            )

        if not markdown_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Markdown files found to check.",
                issues_count=0,
            )

        # Use relative paths and set cwd to the common parent
        cwd: str | None = self.get_cwd(paths=markdown_files)
        logger.debug(f"[MarkdownlintTool] Working directory: {cwd}")
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in markdown_files
        ]

        # Apply line_length configuration if set
        line_length = self.options.get("line_length")
        if line_length:
            self._ensure_markdownlint_config(cwd=cwd, line_length=line_length)

        # Build command
        cmd: list[str] = self._get_markdownlint_command()
        cmd.extend(rel_files)

        logger.debug(f"[MarkdownlintTool] Running: {' '.join(cmd)} (cwd={cwd})")

        timeout_val: int = self.options.get("timeout", MARKDOWNLINT_DEFAULT_TIMEOUT)
        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=timeout_val,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            timeout_msg = (
                f"Markdownlint execution timed out ({timeout_val}s limit exceeded).\n\n"
                "This may indicate:\n"
                "  - Large codebase taking too long to process\n"
                "  - Need to increase timeout via --tool-options markdownlint:timeout=N"
            )
            return ToolResult(
                name=self.name,
                success=False,
                output=timeout_msg,
                issues_count=1,
            )

        # Parse output
        issues = parse_markdownlint_output(output=output)
        issues_count: int = len(issues)
        success_flag: bool = success and issues_count == 0

        # Suppress output when no issues found
        if success_flag:
            output = None

        return ToolResult(
            name=self.name,
            success=success_flag,
            output=output,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Markdownlint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix.

        Returns:
            ToolResult: Result indicating that fixing is not supported.
        """
        return ToolResult(
            name=self.name,
            success=False,
            output=(
                "Markdownlint is a linter only and cannot fix issues. Use a Markdown "
                "formatter like Prettier for formatting."
            ),
            issues_count=0,
        )
