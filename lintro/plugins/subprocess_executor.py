"""Subprocess execution utilities for tool plugins.

This module provides safe subprocess execution with validation and streaming.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False
import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Cache for compiled binary detection
_IS_COMPILED_BINARY: bool | None = None


def is_compiled_binary() -> bool:
    """Detect if lintro is running as a Nuitka-compiled binary.

    When compiled with Nuitka, sys.executable points to the lintro binary itself,
    not a Python interpreter. We detect this by checking if we can import Nuitka
    runtime modules or by checking the executable name.

    Returns:
        True if running as a compiled binary, False otherwise.
    """
    global _IS_COMPILED_BINARY

    if _IS_COMPILED_BINARY is not None:
        return _IS_COMPILED_BINARY

    # Method 1: Check for Nuitka's __compiled__ marker
    try:
        # Nuitka sets __compiled__ at module level
        import __main__

        if getattr(__main__, "__compiled__", False):
            _IS_COMPILED_BINARY = True
            return True
    except (ImportError, AttributeError):
        pass

    # Method 2: Check if sys.executable looks like our binary (not python)
    exe_name = os.path.basename(sys.executable).lower()
    if exe_name in ("lintro", "lintro.exe", "lintro.bin"):
        _IS_COMPILED_BINARY = True
        return True

    # Method 3: Check if we're running from a Nuitka dist folder
    exe_dir = os.path.dirname(sys.executable)
    if "nuitka" in exe_dir.lower() or "__nuitka" in exe_dir.lower():
        _IS_COMPILED_BINARY = True
        return True

    _IS_COMPILED_BINARY = False
    return False


# Shell metacharacters that could enable command injection or unexpected behavior.
# Using frozenset for immutability and O(1) membership testing.
UNSAFE_SHELL_CHARS: frozenset[str] = frozenset(
    {
        # Command chaining and piping
        ";",  # Command separator
        "&",  # Background execution / AND operator
        "|",  # Pipe
        # Redirection
        ">",  # Output redirection
        "<",  # Input redirection
        # Command substitution and expansion
        "`",  # Backtick command substitution
        "$",  # Variable expansion / command substitution
        # Escape and control characters
        "\\",  # Escape character
        "\n",  # Newline (command separator in some contexts)
        "\r",  # Carriage return
        # Glob and pattern matching
        "*",  # Glob wildcard (match any)
        "?",  # Glob wildcard (match single char)
        "[",  # Character class start
        "]",  # Character class end
        # Brace and subshell expansion
        "{",  # Brace expansion start
        "}",  # Brace expansion end
        "(",  # Subshell start
        ")",  # Subshell end
        # Other shell special characters
        "~",  # Home directory expansion
        "!",  # History expansion
    },
)


def validate_subprocess_command(cmd: list[str]) -> None:
    """Validate a subprocess command for safety.

    Args:
        cmd: Command and arguments to validate.

    Raises:
        ValueError: If command is invalid or contains unsafe characters.
    """
    if not cmd or not isinstance(cmd, list):
        raise ValueError("Command must be a non-empty list of strings")

    for arg in cmd:
        if not isinstance(arg, str):
            raise ValueError("All command arguments must be strings")
        if any(ch in arg for ch in UNSAFE_SHELL_CHARS):
            raise ValueError("Unsafe character detected in command argument")


def run_subprocess(
    cmd: list[str],
    timeout: float,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Run a subprocess command safely.

    Args:
        cmd: Command and arguments to run.
        timeout: Timeout in seconds.
        cwd: Working directory for command execution.
        env: Environment variables for the subprocess.

    Returns:
        Tuple of (success, output) where success indicates return code 0.

    Raises:
        TimeoutExpired: If command times out.
        FileNotFoundError: If command executable is not found.
    """
    validate_subprocess_command(cmd)

    try:
        result = subprocess.run(  # nosec B603 - args list, shell=False
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        # Preserve partial output from the original exception
        partial_output = ""
        if e.output:
            partial_output = (
                e.output
                if isinstance(e.output, str)
                else e.output.decode(errors="replace")
            )
        if e.stderr:
            stderr = (
                e.stderr
                if isinstance(e.stderr, str)
                else e.stderr.decode(errors="replace")
            )
            partial_output = partial_output + stderr if partial_output else stderr
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=timeout,
            output=partial_output,
        ) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Command not found: {cmd[0]}. "
            f"Please ensure it is installed and in your PATH.",
        ) from e


def run_subprocess_streaming(
    cmd: list[str],
    timeout: float,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    line_handler: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Run a subprocess command with optional line-by-line streaming.

    This function allows real-time output processing by calling the line_handler
    callback for each line of output as it is produced by the subprocess.

    The timeout is enforced during both output reading and process completion,
    preventing indefinite blocking on slow or hanging processes.

    Args:
        cmd: Command and arguments to run.
        timeout: Timeout in seconds.
        cwd: Working directory for command execution.
        env: Environment variables for the subprocess.
        line_handler: Optional callback called for each line of output.

    Returns:
        Tuple of (success, output) where success indicates return code 0.

    Raises:
        TimeoutExpired: If command times out.
        FileNotFoundError: If command executable is not found.
    """
    validate_subprocess_command(cmd)

    try:
        # Use Popen for streaming output  # nosec B603
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
            bufsize=1,  # Line buffering
        )

        output_lines: list[str] = []

        def read_output() -> None:
            """Read output lines in a separate thread."""
            if process.stdout:
                for line in process.stdout:
                    stripped = line.rstrip("\n")
                    output_lines.append(stripped)
                    if line_handler:
                        line_handler(stripped)

        # Use a thread to read output so we can enforce timeout
        reader_thread = threading.Thread(target=read_output, daemon=True)
        reader_thread.start()
        reader_thread.join(timeout=timeout)

        if reader_thread.is_alive():
            # Timeout occurred during reading - kill the process
            process.kill()
            try:
                process.wait(timeout=1.0)  # Brief timeout for cleanup
            except subprocess.TimeoutExpired:
                pass  # Process didn't die cleanly, but we've done our best
            raise subprocess.TimeoutExpired(
                cmd=cmd,
                timeout=timeout,
                output="\n".join(output_lines),
            )

        # Reading completed, now wait for process to finish
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)
            raise subprocess.TimeoutExpired(
                cmd=cmd,
                timeout=timeout,
                output="\n".join(output_lines),
            )
        return returncode == 0, "\n".join(output_lines)

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Command not found: {cmd[0]}. "
            f"Please ensure it is installed and in your PATH.",
        ) from e
