"""Base core implementation for Lintro."""

import os
import shutil
import subprocess  # nosec B404 - subprocess used safely with shell=False
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult

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
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
    "*.egg-info",
]


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
    can_fix: bool
    config: ToolConfig = field(default_factory=ToolConfig)
    exclude_patterns: list[str] = field(default_factory=list)
    include_venv: bool = False

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
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
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

    def _setup_defaults(self) -> None:
        """Set up default core options and patterns."""
        # Add default exclude patterns if not already present
        for pattern in self._default_exclude_patterns:
            if pattern not in self.exclude_patterns:
                self.exclude_patterns.append(pattern)

        # Add .lintro-ignore patterns (project-wide) if present
        try:
            lintro_ignore_path = os.path.abspath(".lintro-ignore")
            if os.path.exists(lintro_ignore_path):
                with open(lintro_ignore_path, "r", encoding="utf-8") as f:
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
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> tuple[bool, str]:
        """Run a subprocess command.

        Args:
            cmd: list[str]: Command to run.
            timeout: int | None: Command timeout in seconds (defaults to core's \
                timeout).
            cwd: str | None: Working directory to run the command in (optional).

        Returns:
            tuple[bool, str]: Tuple of (success, output)
                - success: True if the command succeeded, False otherwise.
                - output: Command output (stdout + stderr).

        Raises:
            CalledProcessError: If command fails.
            TimeoutExpired: If command times out.
            FileNotFoundError: If command executable is not found.
        """
        # Validate command arguments for safety prior to execution
        self._validate_subprocess_command(cmd=cmd)

        try:
            result = subprocess.run(  # nosec B603 - args list, shell=False
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
                or self.options.get(
                    "timeout",
                    self._default_timeout,
                ),
                cwd=cwd,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired as e:
            raise subprocess.TimeoutExpired(
                cmd=cmd,
                timeout=timeout
                or self.options.get(
                    "timeout",
                    self._default_timeout,
                ),
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

    def set_options(self, **kwargs) -> None:
        """Set core options.

        Args:
            **kwargs: Tool-specific options.

        Raises:
            ValueError: If an option value is invalid.
        """
        for key, value in kwargs.items():
            if key == "timeout" and not isinstance(value, (int, type(None))):
                raise ValueError("Timeout must be an integer or None")
            if key == "exclude_patterns" and not isinstance(value, list):
                raise ValueError("Exclude patterns must be a list")
            if key == "include_venv" and not isinstance(value, bool):
                raise ValueError("Include venv must be a boolean")

        # Update options dict
        self.options.update(kwargs)

        # Update specific attributes for exclude_patterns and include_venv
        if "exclude_patterns" in kwargs:
            self.exclude_patterns = kwargs["exclude_patterns"]
        if "include_venv" in kwargs:
            self.include_venv = kwargs["include_venv"]

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
        """Return the common parent directory for the given paths, or None if not
        applicable.

        Args:
            paths: list[str]: List of file paths to find common parent directory for.

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

    def _get_executable_command(
        self,
        tool_name: str,
    ) -> list[str]:
        """Get the command prefix to execute a tool.

        Prefer running via ``uv run`` when available to ensure the tool executes
        within the active Python environment, avoiding PATH collisions with
        user-level shims. Fall back to a direct executable when ``uv`` is not
        present, and finally to the bare tool name.

        Args:
            tool_name: str: Name of the tool executable to find.

        Returns:
            list[str]: Command prefix to execute the tool.

        Examples:
            >>> self._get_executable_command("ruff")
            ["uv", "run", "ruff"]  # preferred when uv is available

            >>> self._get_executable_command("ruff")
            ["ruff"]  # if uv is not available but the tool is on PATH
        """
        # Tool-specific preferences to balance reliability vs. historical expectations
        python_tools_prefer_uv = {"black", "bandit", "yamllint", "darglint"}

        # Ruff: keep historical expectation for tests (direct invocation first)
        if tool_name == "ruff":
            if shutil.which(tool_name):
                return [tool_name]
            if shutil.which("uv"):
                return ["uv", "run", tool_name]
            return [tool_name]

        # Black: prefer system binary first, then project env via uv run,
        # and finally uvx as a last resort.
        if tool_name == "black":
            if shutil.which(tool_name):
                return [tool_name]
            if shutil.which("uv"):
                return ["uv", "run", tool_name]
            if shutil.which("uvx"):
                return ["uvx", tool_name]
            return [tool_name]

        # Python-based tools where running inside env avoids PATH shim issues
        if tool_name in python_tools_prefer_uv:
            if shutil.which(tool_name):
                return [tool_name]
            if shutil.which("uvx"):
                return ["uvx", tool_name]
            if shutil.which("uv"):
                return ["uv", "run", tool_name]
            return [tool_name]

        # Default: prefer direct system executable (node/binary tools like
        # prettier, hadolint, actionlint)
        if shutil.which(tool_name):
            return [tool_name]
        if shutil.which("uv"):
            return ["uv", "run", tool_name]
        return [tool_name]

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
        ...
