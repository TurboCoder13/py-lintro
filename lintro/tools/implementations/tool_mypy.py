"""Mypy static type checker integration."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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

MYPY_DEFAULT_EXCLUDE_PATTERNS = [
    "tests/*",
    "tests/**",
    "*/tests/*",
    "*/tests/**",
    "test_samples/*",
    "test_samples/**",
    "*/test_samples/*",
    "*/test_samples/**",
    "node_modules/**",
    "dist/**",
    "build/**",
]


def _load_mypy_pyproject_config() -> dict[str, Any]:
    """Return the [tool.mypy] config from pyproject.toml if present.

    Returns:
        dict[str, Any]: Parsed [tool.mypy] table, or empty dict if missing.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        return {}
    try:
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data.get("tool", {}).get("mypy", {}) or {}


def _regex_to_glob(pattern: str) -> str:
    """Coerce a simple regex pattern to a fnmatch glob.

    Args:
        pattern: Regex-style pattern to coerce.

    Returns:
        str: A best-effort fnmatch-style glob pattern.
    """
    cleaned = pattern.strip()
    if cleaned.startswith("^"):
        cleaned = cleaned[1:]
    if cleaned.endswith("$"):
        cleaned = cleaned[:-1]
    cleaned = cleaned.replace(".*", "*")
    if cleaned.endswith("/"):
        cleaned = f"{cleaned}**"
    return cleaned


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
                "strict": False,
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

        if self.options.get("strict") is True:
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

        config_data = _load_mypy_pyproject_config()
        configured_files = config_data.get("files")
        configured_excludes = config_data.get("exclude")

        target_paths: list[str] = list(paths) if paths else []
        if (not target_paths or target_paths == ["."]) and configured_files:
            if isinstance(configured_files, str):
                target_paths = [configured_files]
            elif isinstance(configured_files, list):
                target_paths = [
                    str(path) for path in configured_files if str(path).strip()
                ]

        if not target_paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        self._validate_paths(paths=target_paths)

        effective_excludes: list[str] = list(self.exclude_patterns)
        if configured_excludes:
            raw_excludes = (
                [configured_excludes]
                if isinstance(configured_excludes, str)
                else list(configured_excludes)
            )
            for pattern in raw_excludes:
                glob_pattern = _regex_to_glob(str(pattern))
                if glob_pattern and glob_pattern not in effective_excludes:
                    effective_excludes.append(glob_pattern)

        for default_pattern in MYPY_DEFAULT_EXCLUDE_PATTERNS:
            if default_pattern not in effective_excludes:
                effective_excludes.append(default_pattern)

        python_files = walk_files_with_excludes(
            paths=target_paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=effective_excludes,
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

        if not self.options.get("config_file") and Path("pyproject.toml").exists():
            self.options["config_file"] = str(Path("pyproject.toml").resolve())

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
