"""Base core implementation for Lintro."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - subprocess used safely with shell=False
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import cast

from loguru import logger

from lintro.config.lintro_config import LintroConfig
from lintro.enums.tool_name import ToolName
from lintro.enums.tool_option_key import ToolOptionKey
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.utils.path_filtering import walk_files_with_excludes
from lintro.utils.path_utils import find_lintro_ignore

# Constants for default values
DEFAULT_TIMEOUT: int = 30
DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*cache*",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
    "*.egg-info",
]


@dataclass
class ExecutionContext:
    """Context for tool execution containing prepared files and metadata.

    This dataclass encapsulates the common preparation steps needed before
    running a tool, eliminating duplicate boilerplate across tool implementations.

    Attributes:
        files: List of absolute file paths to process.
        rel_files: List of file paths relative to cwd.
        cwd: Working directory for command execution.
        early_result: If set, return this result immediately (e.g., version check
            failed, no files found).
        timeout: Timeout value for subprocess execution.
    """

    files: list[str] = field(default_factory=list)
    rel_files: list[str] = field(default_factory=list)
    cwd: str | None = None
    early_result: ToolResult | None = None
    timeout: int = DEFAULT_TIMEOUT

    @property
    def should_skip(self) -> bool:
        """Check if execution should be skipped due to early result.

        Returns:
            bool: True if early_result is set and execution should be skipped.
        """
        return self.early_result is not None


@dataclass
class BaseTool(ABC):
    """Base class for all tools.

    This class provides common functionality for all tools and implements
    the Tool protocol. Tool implementations should inherit from this class
    and implement the abstract methods.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the core can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
        _default_timeout: int: Default timeout for core execution in seconds.
        _default_exclude_patterns: list[str]: Default patterns to exclude.

    Raises:
        ValueError: If the configuration is invalid.
    """

    name: str
    description: str
    can_fix: bool = field(default=False)
    config: ToolConfig = field(default_factory=ToolConfig)
    exclude_patterns: list[str] = field(default_factory=list)
    include_venv: bool = field(default=False)

    _default_timeout: int = DEFAULT_TIMEOUT
    _default_exclude_patterns: list[str] = field(
        default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS,
    )

    def __post_init__(self) -> None:
        """Initialize core options and validate configuration."""
        self.options: dict[str, object] = {}
        self._validate_config()
        self._setup_defaults()

    def _validate_config(self) -> None:
        """Validate core configuration.

        Raises:
            ValueError: If the configuration is invalid.
        """
        if self.name == "":
            raise ValueError("Tool name cannot be empty")
        if self.description == "":
            raise ValueError("Tool description cannot be empty")
        if not isinstance(self.config, ToolConfig):
            raise ValueError("Tool config must be a ToolConfig instance")
        if not isinstance(self.config.priority, int):
            raise ValueError("Tool priority must be an integer")
        if not isinstance(self.config.conflicts_with, list):
            raise ValueError("Tool conflicts_with must be a list")
        if not isinstance(self.config.file_patterns, list):
            raise ValueError("Tool file_patterns must be a list")
        if not isinstance(self.config.tool_type, ToolType):
            raise ValueError("Tool tool_type must be a ToolType instance")

    def _find_lintro_ignore(self) -> str | None:
        """Find .lintro-ignore file by searching upward from current directory.

        Uses the shared utility function to ensure consistent behavior.

        Returns:
            str | None: Path to .lintro-ignore file if found, None otherwise.
        """
        lintro_ignore_path = find_lintro_ignore()
        return str(lintro_ignore_path) if lintro_ignore_path else None

    def _setup_defaults(self) -> None:
        """Set up default core options and patterns."""
        # Add default exclude patterns if not already present
        for pattern in self._default_exclude_patterns:
            if pattern not in self.exclude_patterns:
                self.exclude_patterns.append(pattern)

        # Add .lintro-ignore patterns (project-wide) if present
        # Search upward from current directory to find project root
        try:
            lintro_ignore_path = self._find_lintro_ignore()
            if lintro_ignore_path and os.path.exists(lintro_ignore_path):
                with open(lintro_ignore_path, encoding="utf-8") as f:
                    for line in f:
                        line_stripped = line.strip()
                        if not line_stripped or line_stripped.startswith("#"):
                            continue
                        if line_stripped not in self.exclude_patterns:
                            self.exclude_patterns.append(line_stripped)
        except Exception as e:
            # Non-fatal if ignore file can't be read
            logger.debug(f"Could not read .lintro-ignore: {e}")

        # Load default options from config
        if hasattr(self.config, "options") and self.config.options:
            for key, value in self.config.options.items():
                if key not in self.options:
                    self.options[key] = value

        # Set default timeout if not specified
        if "timeout" not in self.options:
            self.options["timeout"] = self._default_timeout

    def _run_subprocess(
        self,
        cmd: list[str],
        timeout: int | float | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        """Run a subprocess command.

        Args:
            cmd: list[str]: Command to run.
            timeout: int | float | None: Command timeout in seconds \
                (defaults to core's timeout).
            cwd: str | None: Working directory to run the command in (optional).

        Returns:
            tuple[bool, str]: Tuple of (success, output)
                - success: True if the command succeeded, False otherwise.
                - output: Command output (stdout + stderr).

        Raises:
            CalledProcessError: If command fails.
            TimeoutExpired: If command times out.
            FileNotFoundError: If command executable is not found.
            ValueError: If timeout is not numeric.
        """
        # Validate command arguments for safety prior to execution
        self._validate_subprocess_command(cmd=cmd)

        raw_timeout = (
            timeout
            if timeout is not None
            else self.options.get(
                "timeout",
                self._default_timeout,
            )
        )
        if not isinstance(raw_timeout, (int, float)):
            raise ValueError("Timeout must be a number")
        effective_timeout: float = float(raw_timeout)

        try:
            result = subprocess.run(  # nosec B603 - args list, shell=False
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired as e:
            raise subprocess.TimeoutExpired(
                cmd=cmd,
                timeout=effective_timeout,
                output=str(e),
            ) from e
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(
                returncode=e.returncode,
                cmd=cmd,
                output=e.output,
                stderr=e.stderr,
            ) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Command not found: {cmd[0]}. "
                f"Please ensure it is installed and in your PATH.",
            ) from e

    def _validate_subprocess_command(self, cmd: list[str]) -> None:
        """Validate a subprocess command argument list for safety.

        Ensures that the command is a non-empty list of strings and that no
        argument contains shell metacharacters that could enable command
        injection when passed to subprocess (even with ``shell=False``).

        Args:
            cmd: list[str]: Command and arguments to validate.

        Raises:
            ValueError: If the command list is empty, contains non-strings,
                or contains unsafe characters.
        """
        if not cmd or not isinstance(cmd, list):
            raise ValueError("Command must be a non-empty list of strings")

        unsafe_chars: set[str] = {";", "&", "|", ">", "<", "`", "$", "\\", "\n", "\r"}

        for arg in cmd:
            if not isinstance(arg, str):
                raise ValueError("All command arguments must be strings")
            if any(ch in arg for ch in unsafe_chars):
                raise ValueError("Unsafe character detected in command argument")

    def set_options(self, **kwargs: object) -> None:
        """Set core options.

        Args:
            **kwargs: Tool-specific options.

        Raises:
            ValueError: If an option value is invalid.
        """
        for key, value in kwargs.items():
            if key == ToolOptionKey.TIMEOUT.value:
                if value is not None and not isinstance(value, (int, float)):
                    raise ValueError("Timeout must be a number or None")
                # Coerce to float for consistency with _run_subprocess
                kwargs[key] = float(value) if value is not None else None
            if key == ToolOptionKey.EXCLUDE_PATTERNS.value and not isinstance(
                value,
                list,
            ):
                raise ValueError("Exclude patterns must be a list")
            if key == ToolOptionKey.INCLUDE_VENV.value and not isinstance(value, bool):
                raise ValueError("Include venv must be a boolean")

        # Update options dict
        self.options.update(kwargs)

        # Update specific attributes for exclude_patterns and include_venv
        if ToolOptionKey.EXCLUDE_PATTERNS.value in kwargs:
            self.exclude_patterns = cast(
                list[str],
                kwargs[ToolOptionKey.EXCLUDE_PATTERNS.value],
            )
        if ToolOptionKey.INCLUDE_VENV.value in kwargs:
            self.include_venv = cast(bool, kwargs[ToolOptionKey.INCLUDE_VENV.value])

    def _validate_paths(
        self,
        paths: list[str],
    ) -> None:
        """Validate that paths exist and are accessible.

        Args:
            paths: list[str]: List of paths to validate.

        Raises:
            FileNotFoundError: If any path does not exist.
            PermissionError: If any path is not accessible.
        """
        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")
            if not os.access(path, os.R_OK):
                raise PermissionError(f"Path is not accessible: {path}")

    def get_cwd(
        self,
        paths: list[str],
    ) -> str | None:
        """Return the common parent directory for the given paths.

        Args:
            paths: list[str]: Paths to compute a common parent directory for.

        Returns:
            str | None: Common parent directory path, or None if not applicable.
        """
        if paths:
            parent_dirs: set[str] = {os.path.dirname(os.path.abspath(p)) for p in paths}
            if len(parent_dirs) == 1:
                return parent_dirs.pop()
            else:
                return os.path.commonpath(list(parent_dirs))
        return None

    def _prepare_execution(
        self,
        paths: list[str],
        *,
        no_files_message: str = "No files to check.",
        default_timeout: int | None = None,
        file_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> ExecutionContext:
        """Prepare execution context with common boilerplate steps.

        This method consolidates the repeated pattern across all tool implementations:
        1. Verify tool version requirements
        2. Validate input paths
        3. Discover files matching patterns
        4. Compute working directory and relative paths

        Args:
            paths: Input paths to process.
            no_files_message: Message when no files are found.
            default_timeout: Default timeout override (uses tool's default
                if None).
            file_patterns: Override file patterns (uses config patterns
                if None).
            exclude_patterns: Override exclude patterns (uses instance
                patterns if None).

        Returns:
            ExecutionContext: Context with files, cwd, and optional early_result.

        Example:
            ctx = self._prepare_execution(paths)
            if ctx.should_skip:
                return ctx.early_result

            cmd = self._build_command(ctx.rel_files)
            success, output = self._run_subprocess(
                cmd, timeout=ctx.timeout, cwd=ctx.cwd
            )
        """
        # Step 1: Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return ExecutionContext(early_result=version_result)

        # Step 2: Validate paths
        self._validate_paths(paths=paths)
        if not paths:
            return ExecutionContext(
                early_result=ToolResult(
                    name=self.name,
                    success=True,
                    output=no_files_message,
                    issues_count=0,
                ),
            )

        # Step 3: Discover files
        effective_patterns = file_patterns or self.config.file_patterns
        effective_excludes = exclude_patterns or self.exclude_patterns

        files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=effective_patterns,
            exclude_patterns=effective_excludes,
            include_venv=self.include_venv,
        )

        if not files:
            # Customize message based on file type
            file_type = "files"
            if effective_patterns:
                # Extract file types from patterns for a friendlier message
                extensions = [
                    p.replace("*", "") for p in effective_patterns if p.startswith("*.")
                ]
                if extensions:
                    file_type = "/".join(extensions) + " files"

            return ExecutionContext(
                early_result=ToolResult(
                    name=self.name,
                    success=True,
                    output=f"No {file_type} found to check.",
                    issues_count=0,
                ),
            )

        logger.debug(f"Files to process: {files}")

        # Step 4: Compute cwd and relative paths
        cwd: str | None = self.get_cwd(paths=files)
        rel_files: list[str] = [os.path.relpath(f, cwd) if cwd else f for f in files]

        # Step 5: Determine timeout
        timeout_val = default_timeout or self.options.get(
            "timeout",
            self._default_timeout,
        )
        # Ensure timeout is an integer (options dict values are typed as object)
        if isinstance(timeout_val, int):
            timeout = timeout_val
        elif isinstance(timeout_val, (str, float)):
            timeout = int(timeout_val)
        else:
            timeout = self._default_timeout

        return ExecutionContext(
            files=files,
            rel_files=rel_files,
            cwd=cwd,
            timeout=timeout,
        )

    def _get_executable_command(
        self,
        tool_name: str,
    ) -> list[str]:
        """Get the command prefix to execute a tool.

        Uses a unified approach based on tool category:
        - Python bundled tools: Use python -m (guaranteed to use lintro's environment)
        - Node.js tools: Use npx (respects project's package.json)
        - Binary tools: Use system executable

        Args:
            tool_name: str: Name of the tool executable to find.

        Returns:
            list[str]: Command prefix to execute the tool.
        """
        from lintro.enums.tool_name import normalize_tool_name

        # Try to normalize tool_name to ToolName enum for comparison
        # If it's not a valid ToolName, we'll handle it as a binary tool
        try:
            tool_name_enum = normalize_tool_name(tool_name)
        except ValueError:
            # Not a valid ToolName enum - treat as binary tool
            tool_name_enum = None

        # Try each category handler in order
        if cmd := self._get_python_bundled_command(tool_name, tool_name_enum):
            return cmd
        if cmd := self._get_pytest_command(tool_name, tool_name_enum):
            return cmd
        if cmd := self._get_nodejs_command(tool_name, tool_name_enum):
            return cmd
        if cmd := self._get_cargo_command(tool_name, tool_name_enum):
            return cmd

        # Default to binary tool
        return [tool_name]

    def _get_python_bundled_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str] | None:
        """Get command for Python bundled tools.

        Includes: ruff, black, bandit, yamllint, mypy.

        Note: darglint is excluded because it cannot be run as a module.

        Args:
            tool_name: str: Name of the tool executable.
            tool_name_enum: ToolName | None: Normalized tool name enum, if valid.

        Returns:
            list[str] | None: Command prefix if tool is a Python bundled \
                tool, None otherwise.
        """
        import sys

        # Python tools bundled with lintro (guaranteed in our environment)
        # Note: darglint cannot be run as a module (python -m darglint fails)
        python_bundled_tools = {
            ToolName.RUFF,
            ToolName.BLACK,
            ToolName.BANDIT,
            ToolName.YAMLLINT,
            ToolName.MYPY,
        }
        if tool_name_enum in python_bundled_tools:
            # Use python -m to ensure we use the tool from lintro's environment
            python_exe = sys.executable
            if python_exe:
                return [python_exe, "-m", tool_name]
            # Fallback to direct executable if python path not found
            return [tool_name]
        return None

    def _get_pytest_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str] | None:
        """Get command for pytest (user environment tool).

        Args:
            tool_name: str: Name of the tool executable.
            tool_name_enum: ToolName | None: Normalized tool name enum, if valid.

        Returns:
            list[str] | None: Command prefix if tool is pytest, None otherwise.
        """
        import sys

        # Pytest: user environment tool (not bundled)
        if tool_name_enum == ToolName.PYTEST:
            # Use python -m pytest for cross-platform compatibility
            python_exe = sys.executable
            if python_exe:
                return [python_exe, "-m", "pytest"]
            # Fall back to direct executable
            return [tool_name]
        return None

    def _get_nodejs_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str] | None:
        """Get command for Node.js tools (biome, prettier).

        Args:
            tool_name: str: Name of the tool executable.
            tool_name_enum: ToolName | None: Normalized tool name enum, if valid.

        Returns:
            list[str] | None: Command prefix if tool is a Node.js tool, None otherwise.
        """
        # Node.js tools: use npx to respect project's package.json
        nodejs_package_names = {
            ToolName.BIOME: "@biomejs/biome",
            ToolName.PRETTIER: "prettier",
        }
        if tool_name_enum in nodejs_package_names:
            if shutil.which("npx"):
                return ["npx", nodejs_package_names[tool_name_enum]]
            # Fall back to direct executable
            return [tool_name]
        return None

    def _get_cargo_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str] | None:
        """Get command for Cargo/Rust tools.

        Args:
            tool_name: str: Name of the tool executable.
            tool_name_enum: ToolName | None: Normalized tool name enum, if valid.

        Returns:
            list[str] | None: Command prefix if tool is a Cargo tool, None otherwise.
        """
        # Rust/Cargo tools: use system executable
        if tool_name_enum == ToolName.CLIPPY:
            return ["cargo", "clippy"]
        cargo_tools = {"cargo"}  # cargo itself, not a lintro tool
        if tool_name in cargo_tools:
            return [tool_name]
        return None

    def _verify_tool_version(self) -> ToolResult | None:
        """Verify that the tool meets minimum version requirements.

        Returns:
            Optional[ToolResult]: None if version check passes, or a skip result
                if it fails
        """
        from lintro.tools.core.version_requirements import check_tool_version

        command = self._get_executable_command(self.name)
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

    # -------------------------------------------------------------------------
    # Lintro Config Support - Tiered Model
    # -------------------------------------------------------------------------

    def _get_lintro_config(self) -> LintroConfig:
        """Get the current Lintro configuration.

        Returns:
            LintroConfig: Current Lintro configuration instance.
        """
        from lintro.tools.core.config_injection import _get_lintro_config

        return _get_lintro_config()

    def _get_enforced_settings(self) -> dict[str, object]:
        """Get enforced settings as a dictionary.

        Returns:
            dict[str, object]: Dictionary of enforced settings.
        """
        from lintro.tools.core.config_injection import _get_enforced_settings

        return _get_enforced_settings(lintro_config=self._get_lintro_config())

    def _get_enforce_cli_args(self) -> list[str]:
        """Get CLI arguments for enforced settings.

        Returns:
            list[str]: CLI arguments to inject enforced settings.
        """
        from lintro.tools.core.config_injection import _get_enforce_cli_args

        return _get_enforce_cli_args(
            tool_name=self.name,
            lintro_config=self._get_lintro_config(),
        )

    def _get_defaults_config_args(self) -> list[str]:
        """Get CLI arguments for defaults config injection.

        Returns:
            list[str]: CLI arguments to inject defaults config file.
        """
        from lintro.tools.core.config_injection import _get_defaults_config_args

        return _get_defaults_config_args(
            tool_name=self.name,
            lintro_config=self._get_lintro_config(),
        )

    def _should_use_lintro_config(self) -> bool:
        """Check if Lintro config should be used for this tool.

        Returns:
            bool: True if Lintro config should be injected.
        """
        from lintro.tools.core.config_injection import _should_use_lintro_config

        return _should_use_lintro_config(tool_name=self.name)

    def _build_config_args(self) -> list[str]:
        """Build combined CLI arguments for config injection.

        Combines enforce CLI args and defaults config args.

        Returns:
            list[str]: Combined CLI arguments for config injection.
        """
        from lintro.tools.core.config_injection import _build_config_args

        return _build_config_args(
            tool_name=self.name,
            lintro_config=self._get_lintro_config(),
        )

    @abstractmethod
    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files for issues.

        Args:
            paths: list[str]: List of file paths to check.

        Returns:
            ToolResult: ToolResult instance.

        Raises:
            FileNotFoundError: If any path does not exist or is not accessible.
            subprocess.TimeoutExpired: If the core execution times out.
            subprocess.CalledProcessError: If the core execution fails.
        """
        ...

    @abstractmethod
    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files.

        Args:
            paths: list[str]: List of file paths to fix.

        Raises:
            NotImplementedError: If the core does not support fixing issues.
        """
        if not self.can_fix:
            raise NotImplementedError(f"{self.name} does not support fixing issues")
        raise NotImplementedError("Subclasses must implement fix()")
