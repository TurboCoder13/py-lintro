"""
standard_tool.py

StandardTool base class for unified tool implementation.

This class provides standard subprocess execution, timeout handling, success detection,
and option validation for most tool integrations in Lintro.

"""
from __future__ import annotations
import subprocess
import shlex
from dataclasses import field
from typing import Any

class StandardTool:
    """Base class for standard tool implementations.

    Provides subprocess execution, timeout, success detection, and option validation.
    """

    name: str
    timeout: int = 30
    options: dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, timeout: int = 30, options: dict[str, Any] | None = None) -> None:
        """Initialize the StandardTool.

        Args:
            name (str): Tool name.
            timeout (int): Timeout in seconds.
            options (dict[str, Any] | None): Tool options.
        """
        self.name = name
        self.timeout = timeout
        self.options = options if options is not None else {}

    def run(self, command: str | list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
        """Run the tool subprocess with timeout.

        Args:
            command (str | list[str]): Command to execute.
            cwd (str | None): Working directory.

        Returns:
            subprocess.CompletedProcess: The completed process object.
        """
        if isinstance(command, str):
            command = shlex.split(command)
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{self.name} timed out after {self.timeout} seconds") from exc
        return result

    def is_success(self, process: subprocess.CompletedProcess) -> bool:
        """Determine if the tool run was successful.

        Args:
            process (subprocess.CompletedProcess): The completed process.

        Returns:
            bool: True if successful, False otherwise.
        """
        return process.returncode == 0

    def validate_options(self) -> None:
        """Validate tool options. Override for custom validation."""
        # Example: Ensure all options are of expected type (str/int/bool)
        for key, value in self.options.items():
            if not isinstance(value, (str, int, bool)):
                raise ValueError(f"Invalid option type for {key}: {type(value)}") 