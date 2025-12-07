"""Mypy static type checker integration."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False
from dataclasses import dataclass, field

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.mypy.mypy_parser import parse_mypy_output
from lintro.tools.core.timeout_utils import (
    create_timeout_result,
    get_timeout_value,
    run_subprocess_with_timeout,
)
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

MYPY_DEFAULT_TIMEOUT = 60
MYPY_DEFAULT_PRIORITY = 82
MYPY_FILE_PATTERNS = ["*.py", "*.pyi"]


@dataclass
class MypyTool(BaseTool):
    """Mypy static type checker integration."""

    name: str = "mypy"
    description: str = "Static type checker for Python"
    can_fix: bool = False
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=MYPY_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=MYPY_FILE_PATTERNS,
            tool_type=ToolType.LINTER | ToolType.TYPE_CHECKER,
            options={
                "timeout": MYPY_DEFAULT_TIMEOUT,
                "strict": True,
                "ignore_missing_imports": True,
                "python_version": None,
                "config_file": None,
                "cache_dir": None,
            },
        ),
    )

    def set_options(
        self,
        strict: bool | None = None,
        ignore_missing_imports: bool | None = None,
        python_version: str | None = None,
        config_file: str | None = None,
        cache_dir: str | None = None,
        **kwargs,
    ) -> None:
        """Set mypy-specific options.

        Args:
            strict: Enable mypy ``--strict`` mode when True.
            ignore_missing_imports: Toggle ``--ignore-missing-imports``.
            python_version: Target python version string (e.g., ``3.13``).
            config_file: Optional path to a mypy configuration file.
            cache_dir: Optional path to mypy cache directory.
            **kwargs: Additional options forwarded to ``BaseTool.set_options``.

        Raises:
            ValueError: If any provided option is of an unexpected type.
        """
        if strict is not None and not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")
        if ignore_missing_imports is not None and not isinstance(
            ignore_missing_imports,
            bool,
        ):
            raise ValueError("ignore_missing_imports must be a boolean")
        if python_version is not None and not isinstance(python_version, str):
            raise ValueError("python_version must be a string")
        if config_file is not None and not isinstance(config_file, str):
            raise ValueError("config_file must be a string path")
        if cache_dir is not None and not isinstance(cache_dir, str):
            raise ValueError("cache_dir must be a string path")

        options = {
            "strict": strict,
            "ignore_missing_imports": ignore_missing_imports,
            "python_version": python_version,
            "config_file": config_file,
            "cache_dir": cache_dir,
        }
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self, files: list[str]) -> list[str]:
        """Build the mypy invocation command.

        Args:
            files: Relative file paths that should be checked by mypy.

        Returns:
            A list of command arguments ready to be executed.
        """
        cmd: list[str] = self._get_executable_command(tool_name="mypy")
        cmd.extend(
            [
                "--output",
                "json",
                "--show-error-codes",
                "--show-column-numbers",
                "--hide-error-context",
                "--no-error-summary",
                "--explicit-package-bases",
            ],
        )

        if self.options.get("strict", True):
            cmd.append("--strict")
        if self.options.get("ignore_missing_imports", True):
            cmd.append("--ignore-missing-imports")

        if self.options.get("python_version"):
            cmd.extend(["--python-version", str(self.options["python_version"])])
        if self.options.get("config_file"):
            cmd.extend(["--config-file", str(self.options["config_file"])])
        if self.options.get("cache_dir"):
            cmd.extend(["--cache-dir", str(self.options["cache_dir"])])

        cmd.extend(files)
        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Run mypy type checking.

        Args:
            paths: Paths or files to type-check.

        Returns:
            A ``ToolResult`` describing the check outcome.
        """
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

        cwd = self.get_cwd(paths=python_files)
        rel_files = [os.path.relpath(f, cwd) if cwd else f for f in python_files]

        timeout = get_timeout_value(self, MYPY_DEFAULT_TIMEOUT)
        cmd = self._build_command(files=rel_files)

        try:
            success, output = run_subprocess_with_timeout(
                tool=self,
                cmd=cmd,
                timeout=timeout,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=timeout,
                cmd=cmd,
            )
            return ToolResult(
                name=self.name,
                success=timeout_result["success"],
                output=timeout_result["output"],
                issues_count=timeout_result["issues_count"],
                issues=timeout_result["issues"],
            )

        issues = parse_mypy_output(output=output)
        issues_count = len(issues)

        if not success and issues_count == 0:
            # Execution failed but no structured issues were parsed; surface raw output
            return ToolResult(
                name=self.name,
                success=False,
                output=output or "mypy execution failed.",
                issues_count=0,
            )

        return ToolResult(
            name=self.name,
            success=issues_count == 0,
            output=None,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Mypy does not support auto-fixing.

        Args:
            paths: Paths or files passed for completeness.

        Raises:
            NotImplementedError: Always, because mypy cannot fix issues.
        """
        raise NotImplementedError("mypy does not support auto-fixing")
