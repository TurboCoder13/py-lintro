"""Yamllint YAML linter integration."""

import fnmatch
import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from lintro.enums.tool_type import ToolType
from lintro.enums.yamllint_format import (
    YamllintFormat,
    normalize_yamllint_format,
)
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.path_filtering import walk_files_with_excludes

# Constants
YAMLLINT_DEFAULT_TIMEOUT: int = 15
YAMLLINT_DEFAULT_PRIORITY: int = 40
YAMLLINT_FILE_PATTERNS: list[str] = [
    "*.yml",
    "*.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".yamllint.yaml",
]
YAMLLINT_FORMATS: tuple[str, ...] = tuple(m.name.lower() for m in YamllintFormat)

# Cache the yamllint parser import to avoid repeated try/except overhead
_yamllint_parser: object | None = None


def _get_yamllint_parser() -> Any | None:
    """Get the yamllint parser function, caching the import result.

    Returns:
        The parse_yamllint_output function if available, None otherwise.
    """
    global _yamllint_parser
    if _yamllint_parser is None:
        try:
            from lintro.parsers.yamllint.yamllint_parser import (
                parse_yamllint_output,
            )

            _yamllint_parser = parse_yamllint_output
        except ImportError:
            _yamllint_parser = (
                False  # Use False to distinguish from None (not yet tried)
            )
    return _yamllint_parser if _yamllint_parser is not False else None


@dataclass
class YamllintTool(BaseTool):
    """Yamllint YAML linter integration.

    Yamllint is a linter for YAML files that checks for syntax errors,
    formatting issues, and other YAML best practices.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = field(default="yamllint")
    description: str = field(default="YAML linter for syntax and style checking")
    can_fix: bool = field(default=False)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=YAMLLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=YAMLLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
            options={
                "timeout": YAMLLINT_DEFAULT_TIMEOUT,
                # Use parsable by default; aligns with parser expectations
                "format": "parsable",
                "config_file": None,
                "config_data": None,
                "strict": False,
                "relaxed": False,
                "no_warnings": False,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool."""
        super().__post_init__()

    def set_options(  # type: ignore[override]
        self,
        format: str | YamllintFormat | None = None,
        config_file: str | None = None,
        config_data: str | None = None,
        strict: bool | None = None,
        relaxed: bool | None = None,
        no_warnings: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Yamllint-specific options.

        Args:
            format: Output format (parsable, standard, colored, github, auto)
            config_file: Path to yamllint config file
            config_data: Inline config data (YAML string)
            strict: Return non-zero exit code on warnings as well as errors
            relaxed: Use relaxed configuration
            no_warnings: Output only error level problems
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if format is not None:
            # Accept both enum and string values for backward compatibility
            fmt_enum = normalize_yamllint_format(format)
            format = fmt_enum.name.lower()
        if config_file is not None and not isinstance(config_file, str):
            raise ValueError("config_file must be a string path")
        if config_data is not None and not isinstance(config_data, str):
            raise ValueError("config_data must be a YAML string")
        if strict is not None and not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")
        if relaxed is not None and not isinstance(relaxed, bool):
            raise ValueError("relaxed must be a boolean")
        if no_warnings is not None and not isinstance(no_warnings, bool):
            raise ValueError("no_warnings must be a boolean")
        options = {
            "format": format,
            "config_file": config_file,
            "config_data": config_data,
            "strict": strict,
            "relaxed": relaxed,
            "no_warnings": no_warnings,
        }
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _find_yamllint_config(self, search_dir: str | None = None) -> str | None:
        """Locate yamllint config file if not explicitly provided.

        Yamllint searches upward from the file's directory to find config files,
        so we do the same to match native behavior.

        When config_data is provided via set_options(), it takes precedence over
        any discovered config file. This means file-based discovery is skipped
        entirely when inline config is present.

        Args:
            search_dir: Directory to start searching from. If None, searches from
                current working directory.

        Returns:
            str | None: Path to config file if found, None otherwise.
                Returns None if config_data is set (inline config takes precedence).

        Note:
            Config precedence order:
            1. config_data (inline YAML string) - highest priority
            2. config_file (explicitly set path)
            3. Auto-discovered config files (.yamllint, .yamllint.yml, etc.)
        """
        # If config_file is explicitly set, use it
        config_file = self.options.get("config_file")
        if config_file:
            return str(config_file)

        # If config_data is set, don't search for config file
        # (inline config takes precedence over file-based discovery)
        if self.options.get("config_data"):
            return None

        # Check for config files in order of precedence
        config_paths = [
            ".yamllint",
            ".yamllint.yml",
            ".yamllint.yaml",
        ]
        # Search upward from search_dir (or cwd) to find config, just like yamllint does
        start_dir = os.path.abspath(search_dir) if search_dir else os.getcwd()
        current_dir = start_dir

        # Walk upward from the file's directory to find config
        # Stop at filesystem root to avoid infinite loop
        while True:
            for config_name in config_paths:
                config_path = os.path.join(current_dir, config_name)
                if os.path.exists(config_path):
                    logger.debug(
                        f"[YamllintTool] Found config file: {config_path} "
                        f"(searched from {start_dir})",
                    )
                    return config_path

            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            # Stop if we've reached the filesystem root (parent == current)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        return None

    def _load_yamllint_ignore_patterns(
        self,
        config_file: str | None,
    ) -> list[str]:
        """Load ignore patterns from yamllint config file.

        Yamllint's ignore patterns only work when scanning directories, not when
        individual files are passed. We need to respect these patterns at the
        lintro level by filtering out ignored files before passing them to yamllint.

        Args:
            config_file: Path to yamllint config file, or None.

        Returns:
            list[str]: List of ignore patterns from the config file.
        """
        if not config_file or not os.path.exists(config_file):
            return []

        ignore_patterns: list[str] = []
        if yaml is None:
            logger.debug(
                "[YamllintTool] PyYAML not available, cannot parse ignore patterns",
            )
            return ignore_patterns
        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                if config_data and isinstance(config_data, dict):
                    # Check for ignore patterns in line-length rule
                    line_length_config = config_data.get("rules", {}).get(
                        "line-length",
                        {},
                    )
                    if isinstance(line_length_config, dict):
                        ignore_value = line_length_config.get("ignore")
                        if ignore_value:
                            if isinstance(ignore_value, str):
                                # Multi-line string - split by newlines
                                ignore_patterns.extend(
                                    [
                                        line.strip()
                                        for line in ignore_value.split("\n")
                                        if line.strip()
                                    ],
                                )
                            elif isinstance(ignore_value, list):
                                # List of patterns
                                ignore_patterns.extend(ignore_value)
                    logger.debug(
                        f"[YamllintTool] Loaded {len(ignore_patterns)} ignore patterns "
                        f"from {config_file}: {ignore_patterns}",
                    )
        except Exception as e:
            logger.debug(
                f"[YamllintTool] Failed to load ignore patterns "
                f"from {config_file}: {e}",
            )

        return ignore_patterns

    def _should_ignore_file(
        self,
        file_path: str,
        ignore_patterns: list[str],
    ) -> bool:
        """Check if a file should be ignored based on yamllint ignore patterns.

        Args:
            file_path: Path to the file to check.
            ignore_patterns: List of ignore patterns from yamllint config.

        Returns:
            bool: True if the file should be ignored, False otherwise.
        """
        if not ignore_patterns:
            return False

        # Normalize path separators for cross-platform compatibility
        normalized_path: str = file_path.replace("\\", "/")

        for pattern in ignore_patterns:
            pattern = pattern.strip()
            if not pattern:
                continue
            # Yamllint ignore patterns are directory paths (like .github/workflows/)
            # Check if the pattern appears as a directory path in the file path
            # Handle both relative paths (./.github/workflows/) and absolute paths
            # Pattern should match if it appears as /pattern/ or at the start
            if normalized_path.startswith(pattern):
                return True
            # Check if pattern appears as a directory in the path
            # (handles ./prefix and absolute paths)
            if f"/{pattern}" in normalized_path:
                return True
            # Also try glob matching for patterns with wildcards
            if fnmatch.fnmatch(normalized_path, pattern):
                return True

        return False

    def _build_command(self) -> list[str]:
        """Build the yamllint command.

        Returns:
            list[str]: Command arguments for yamllint.
        """
        cmd: list[str] = self._get_executable_command("yamllint")
        format_option = str(self.options.get("format", YAMLLINT_FORMATS[0]))
        cmd.extend(["--format", format_option])
        # Note: Config file discovery happens per-file in _process_yaml_file
        # since yamllint discovers configs relative to each file
        config_file_opt = self.options.get("config_file")
        if config_file_opt:
            cmd.extend(["--config-file", str(config_file_opt)])
        config_data_opt = self.options.get("config_data")
        if config_data_opt:
            cmd.extend(["--config-data", str(config_data_opt)])
        if self.options.get("strict", False):
            cmd.append("--strict")
        if self.options.get("relaxed", False):
            cmd.append("--relaxed")

        return cmd

    def _process_yaml_file(
        self,
        file_path: str,
        timeout: int,
    ) -> tuple[int, list[Any], bool, bool, bool, bool]:
        """Process a single YAML file with yamllint.

        Args:
            file_path: Path to the YAML file to process.
            timeout: Timeout in seconds for the subprocess call.

        Returns:
            tuple containing:
                - issues_count: Number of issues found
                - issues_list: List of parsed issues
                - skipped_flag: True if file was skipped due to timeout
                - execution_failure_flag: True if there was an execution failure
                - success_flag: False if issues were found
                - should_continue: True if file should be silently skipped
                    (missing file)
        """
        # Use absolute path; run with the file's parent as cwd so that
        # yamllint discovers any local .yamllint config beside the file.
        abs_file: str = os.path.abspath(file_path)
        cwd_result = self.get_cwd(paths=[abs_file])
        file_cwd: str = cwd_result if cwd_result is not None else os.getcwd()
        file_dir: str = os.path.dirname(abs_file)
        # Build command and discover config relative to file's directory
        cmd: list[str] = self._get_executable_command("yamllint")
        format_option = str(self.options.get("format", "parsable"))
        cmd.extend(["--format", format_option])
        # Discover config file relative to the file being checked
        config_file: str | None = self._find_yamllint_config(search_dir=file_dir)
        if config_file:
            # Ensure config file path is absolute so yamllint can find it
            # even when cwd is a subdirectory
            abs_config_file = os.path.abspath(config_file)
            cmd.extend(["--config-file", abs_config_file])
            logger.debug(
                f"[YamllintTool] Using config file: {abs_config_file} "
                f"(original: {config_file})",
            )
        config_data_opt = self.options.get("config_data")
        if config_data_opt:
            cmd.extend(["--config-data", str(config_data_opt)])
        if self.options.get("strict", False):
            cmd.append("--strict")
        if self.options.get("relaxed", False):
            cmd.append("--relaxed")
        if self.options.get("no_warnings", False):
            cmd.append("--no-warnings")

        cmd.append(abs_file)

        # Execute yamllint on the file
        logger.debug(f"[YamllintTool] Processing file: {abs_file} (cwd={file_cwd})")
        logger.debug(f"[YamllintTool] Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(  # nosec B603 - yamllint is a trusted executable
                cmd,
                cwd=file_cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            logger.warning(
                f"[YamllintTool] Timeout ({timeout}s) processing {file_path}",
            )
            return (0, [], True, False, True, False)
        except OSError as e:
            logger.warning(
                f"[YamllintTool] Failed to execute yamllint on {file_path}: {e}",
            )
            return (0, [], False, True, True, False)

        # Parse the output
        issues: list[Any] = []
        issues_count = 0

        if result.returncode != 0:
            # Parse the output to extract issues
            parse_yamllint_output = _get_yamllint_parser()
            if parse_yamllint_output:
                issues = parse_yamllint_output(result.stdout + result.stderr)
                issues_count = len(issues)
            else:
                logger.warning(
                    "[YamllintTool] Could not import yamllint parser, "
                    f"issues may not be properly parsed. Output: {result.stdout}",
                )
                issues_count = 1 if result.returncode != 0 else 0

        success_flag = result.returncode == 0
        return (issues_count, issues, False, False, success_flag, False)

    def _process_yaml_file_result(
        self,
        issues_count: int,
        issues: list[Any],
        skipped_flag: bool,
        execution_failure_flag: bool,
        success_flag: bool,
        file_path: str,
        all_success: bool,
        all_issues: list[Any],
        skipped_files: list[str],
        timeout_skipped_count: int,
        other_execution_failures: int,
        total_issues: int,
    ) -> tuple[bool, list[Any], list[str], int, int, int]:
        """Process the result of processing a single YAML file.

        Args:
            issues_count: Number of issues found in the file.
            issues: List of issues found in the file.
            skipped_flag: True if file was skipped due to timeout.
            execution_failure_flag: True if there was an execution failure.
            success_flag: True if the file processed successfully.
            file_path: Path to the file that was processed.
            all_success: Current overall success status.
            all_issues: Current list of all issues.
            skipped_files: Current list of skipped files.
            timeout_skipped_count: Current count of timeout-skipped files.
            other_execution_failures: Current count of other execution failures.
            total_issues: Current total issues count.

        Returns:
            Updated tuple of (all_success, all_issues, skipped_files,
                timeout_skipped_count, other_execution_failures, total_issues).
        """
        if not success_flag:
            all_success = False
        total_issues += issues_count
        if issues:
            all_issues.extend(issues)
        if skipped_flag:
            skipped_files.append(file_path)
            all_success = False
            timeout_skipped_count += 1
        elif execution_failure_flag:
            # Only count execution failures if not already counted as skipped
            all_success = False
            other_execution_failures += 1
        return (
            all_success,
            all_issues,
            skipped_files,
            timeout_skipped_count,
            other_execution_failures,
            total_issues,
        )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Yamllint.

        Args:
            paths: list[str]: List of file or directory paths to check.

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

        # Use shared utility for file discovery
        yaml_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not yaml_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No YAML files found to check.",
                issues_count=0,
            )

        # Process each YAML file
        all_issues: list[Any] = []
        total_issues = 0
        all_success = True
        skipped_files: list[str] = []
        timeout_skipped_count = 0
        other_execution_failures = 0

        timeout_opt = self.options.get("timeout", YAMLLINT_DEFAULT_TIMEOUT)
        if timeout_opt is not None and not isinstance(timeout_opt, int):
            timeout_val = int(str(timeout_opt))
        elif isinstance(timeout_opt, int):
            timeout_val = timeout_opt
        else:
            timeout_val = YAMLLINT_DEFAULT_TIMEOUT

        # Load ignore patterns from yamllint config before processing files
        config_file = self._find_yamllint_config(search_dir=paths[0] if paths else None)
        ignore_patterns = self._load_yamllint_ignore_patterns(config_file=config_file)

        for file_path in yaml_files:
            if self._should_ignore_file(
                file_path=file_path,
                ignore_patterns=ignore_patterns,
            ):
                continue

            # Process the YAML file
            (
                issues_count,
                issues,
                skipped_flag,
                execution_failure_flag,
                success_flag,
                should_continue,
            ) = self._process_yaml_file(file_path=file_path, timeout=timeout_val)

            if should_continue:
                continue

            (
                all_success,
                all_issues,
                skipped_files,
                timeout_skipped_count,
                other_execution_failures,
                total_issues,
            ) = self._process_yaml_file_result(
                issues_count=issues_count,
                issues=issues,
                skipped_flag=skipped_flag,
                execution_failure_flag=execution_failure_flag,
                success_flag=success_flag,
                file_path=file_path,
                all_success=all_success,
                all_issues=all_issues,
                skipped_files=skipped_files,
                timeout_skipped_count=timeout_skipped_count,
                other_execution_failures=other_execution_failures,
                total_issues=total_issues,
            )

        # Build output message if there are skipped files or execution failures
        output: str | None = None
        if timeout_skipped_count > 0 or other_execution_failures > 0:
            output_lines: list[str] = []
            if timeout_skipped_count > 0:
                output_lines.append(
                    f"Skipped {timeout_skipped_count} file(s) due to timeout "
                    f"({timeout_val}s limit exceeded):",
                )
                for file in skipped_files:
                    output_lines.append(f"  - {file}")
            if other_execution_failures > 0:
                output_lines.append(
                    f"Failed to process {other_execution_failures} file(s) "
                    "due to execution errors",
                )
            output = "\n".join(output_lines) if output_lines else None

        # Include execution failures in issues_count to properly reflect tool
        # failure status (timeouts are tracked separately and not counted as issues)
        total_issues_with_failures = total_issues + other_execution_failures
        return ToolResult(
            name=self.name,
            success=all_success,
            output=output,
            issues_count=total_issues_with_failures,
            issues=all_issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Yamllint cannot fix issues, only report them.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Returns:
            ToolResult: Result indicating that fixing is not supported.
        """
        return ToolResult(
            name=self.name,
            success=False,
            output=(
                "Yamllint is a linter only and cannot fix issues. Use a YAML "
                "formatter like Prettier for formatting."
            ),
            issues_count=0,
        )
