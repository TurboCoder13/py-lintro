"""Pydocstyle docstring style checker integration."""

import os
import subprocess
import sys
import re
from lintro.tools import Tool, ToolConfig


class PydocstyleTool(Tool):
    """Pydocstyle docstring style checker integration."""

    name = "pydocstyle"
    description = "Python docstring style checker that checks compliance with PEP 257"
    can_fix = False  # Pydocstyle can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=45,  # Similar priority to other linters
        conflicts_with=[],  # No direct conflicts
        file_patterns=["*.py"],  # Only applies to Python files
        options={
            "timeout": 10,  # Default timeout in seconds per file
            "convention": "pep257",  # Default convention
        },
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.timeout = self.config.options.get("timeout", 10)
        self.convention = self.config.options.get("convention", "pep257")

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
        convention: str | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 10)
            convention: Docstring style convention to use (default: pep257)
        """
        self.exclude_patterns = exclude_patterns or []
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout
        if convention is not None:
            self.convention = convention

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check files with Pydocstyle.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Process each file individually to prevent hanging on large codebases
        all_outputs = []
        all_success = True
        skipped_files = []
        processed_files = 0

        # Expand directories to individual Python files
        python_files = []
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            # Skip files in excluded patterns
                            if not self._should_exclude(file_path):
                                python_files.append(file_path)
            elif path.endswith(".py"):
                if not self._should_exclude(path):
                    python_files.append(path)

        if not python_files:
            return True, "No Python files found in the specified paths."

        # Process each file with a timeout
        for file_path in python_files:
            processed_files += 1
            try:
                # Use a very simple command with no regex patterns
                cmd = [
                    sys.executable,  # Use the current Python interpreter
                    "-m",
                    "pydocstyle",
                    file_path,
                    "--ignore-decorators=*",  # Avoid regex issues with decorators
                ]

                # Run with timeout
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=os.environ.copy(),  # Use current environment
                )

                try:
                    stdout, stderr = process.communicate(timeout=self.timeout)
                    if process.returncode == 0:
                        # No issues found in this file
                        pass
                    else:
                        # Issues found
                        all_success = False
                        output = stdout or stderr
                        if output:
                            # Format the output to match what format_tool_output expects
                            formatted_output = self._format_raw_output(file_path, output)
                            all_outputs.append(formatted_output)
                except subprocess.TimeoutExpired:
                    process.kill()
                    skipped_files.append(file_path)
                    all_success = False  # Mark as failed if any file times out
                    timeout_msg = f"Skipped {file_path} (timeout after {self.timeout}s)"
                    all_outputs.append(timeout_msg)
            except Exception as e:
                skipped_files.append(file_path)
                all_success = False  # Mark as failed if any file has an error
                all_outputs.append(f"Error processing {file_path}: {str(e)}")

        # Prepare the final output
        if not all_outputs:
            return True, "No docstring style issues found."

        output = "\n".join(all_outputs)
        if skipped_files:
            skip_msg = (
                f"\n\nSkipped {len(skipped_files)} files due to timeout or errors."
            )
            output += skip_msg
        return all_success, output

    def _format_raw_output(self, file_path: str, output: str) -> str:
        """
        Format pydocstyle output to match what format_tool_output expects.

        Args:
            file_path: Path to the file being checked
            output: Raw output from pydocstyle

        Returns:
            Formatted output suitable for format_tool_output
        """
        lines = output.strip().split("\n")
        formatted_lines = []
        
        # pydocstyle output format is typically:
        # /path/to/file.py:123 at module level:
        #     D100: Missing module docstring
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a file:line pattern
            file_line_match = re.match(r".*?:(\d+)", line)
            
            if file_line_match and file_path in line:
                # This is a new error location
                line_num = file_line_match.group(1)
                
                # The next line should contain the error code and message
                if i + 1 < len(lines):
                    code_line = lines[i + 1].strip()
                    code_match = re.match(r"([A-Z]\d+): (.*)", code_line)
                    
                    if code_match:
                        code = code_match.group(1)
                        message = code_match.group(2)
                        
                        # Format the output to match what format_tool_output expects
                        formatted_lines.append(f"{file_path}:{line_num} at module level:")
                        formatted_lines.append(f"    {code}: {message}")
                        
                        # Skip the code line since we've processed it
                        i += 1
            
            i += 1
        
        return "\n".join(formatted_lines)

    def _parse_issues(self, file_path: str, output: str) -> list[dict]:
        """
        Parse pydocstyle output to extract issues.

        Args:
            file_path: Path to the file being checked
            output: Raw output from pydocstyle

        Returns:
            List of issues, each as a dictionary with file, code, line, and message
        """
        lines = output.strip().split("\n")
        issues = []
        
        # pydocstyle output format is typically:
        # /path/to/file.py:123 at module level:
        #     D100: Missing module docstring
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a file:line pattern
            file_line_match = re.match(r".*?:(\d+)", line)
            
            if file_line_match and file_path in line:
                # This is a new error location
                line_num = file_line_match.group(1)
                
                # The next line should contain the error code and message
                if i + 1 < len(lines):
                    code_line = lines[i + 1].strip()
                    code_match = re.match(r"([A-Z]\d+): (.*)", code_line)
                    
                    if code_match:
                        code = code_match.group(1)
                        message = code_match.group(2)
                        
                        # Add the issue to the list
                        issues.append({
                            "file": get_relative_path(file_path),
                            "code": code,
                            "line": line_num,
                            "message": message
                        })
                        
                        # Skip the code line since we've processed it
                        i += 1
            
            i += 1
        
        return issues

    def _format_output(self, file_path: str, output: str) -> str:
        """
        Format pydocstyle output for tabular display.

        Args:
            file_path: Path to the file being checked
            output: Raw output from pydocstyle

        Returns:
            Formatted output suitable for tabular display
        """
        lines = output.strip().split("\n")
        formatted_lines = []

        # Add file header
        formatted_lines.append(f"🔴 File: {file_path}")
        formatted_lines.append(
            "+----------+------+------+------------------------------------------+"
        )
        formatted_lines.append(
            "| Code      | Line | Col  | Message                                  |"
        )
        formatted_lines.append(
            "+----------+------+------+------------------------------------------+"
        )
        
        # Process each error
        current_line = ""
        current_code = ""
        current_message = ""
        
        # pydocstyle output format is typically:
        # /path/to/file.py:123 at module level:
        #     D100: Missing docstring in public module
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a file:line pattern
            file_line_match = re.match(r".*?:(\d+)", line)
            
            if file_line_match and file_path in line:
                # This is a new error location
                current_line = file_line_match.group(1)
                
                # The next line should contain the error code and message
                if i + 1 < len(lines):
                    code_line = lines[i + 1].strip()
                    code_match = re.match(r"([A-Z]\d+): (.*)", code_line)
                    
                    if code_match:
                        current_code = code_match.group(1)
                        current_message = code_match.group(2)
                        
                        # Add the error to the formatted output
                        formatted_lines.append(
                            f"| {current_code:<8} | {current_line:<4} | {'0':<4} | "
                            f"{self._wrap_text(current_message, 40):<40} |"
                        )
                        
                        # Skip the code line since we've processed it
                        i += 1
            
            i += 1
        
        # Add footer
        formatted_lines.append(
            "+----------+------+------+------------------------------------------+"
        )
        
        return "\n".join(formatted_lines)

    def _wrap_text(self, text: str, width: int) -> str:
        """
        Wrap text to fit within a specified width.

        Args:
            text: Text to wrap
            width: Maximum width

        Returns:
            Wrapped text
        """
        if len(text) <= width:
            return text
        return text[:width - 3] + "..."

    def _should_exclude(self, file_path: str) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be excluded, False otherwise
        """
        # Check virtual env exclusion
        if not self.include_venv:
            venv_dirs = [
                ".venv",
                "venv",
                "env",
                "ENV",
                "virtualenv",
                "virtual_env",
                "virtualenvs",
                "site-packages",
                "node_modules",  # Also exclude node_modules
            ]
            # Use path parts to avoid regex issues
            path_parts = file_path.split(os.sep)
            for venv_dir in venv_dirs:
                if venv_dir in path_parts:
                    return True

        # Check user-defined exclusion patterns
        for pattern in self.exclude_patterns:
            # Simple string containment check instead of regex
            if pattern in file_path:
                return True

        return False

    def fix(self, paths: list[str]) -> tuple[bool, str]:
        """
        Fix is not supported for pydocstyle.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
        """
        # Pydocstyle cannot fix issues automatically
        msg = (
            "Pydocstyle cannot automatically fix issues. "
            "Run 'lintro check' to see issues."
        )
        return False, msg

def get_relative_path(path: str) -> str:
    """
    Get the path relative to the current working directory.

    Args:
        path: Absolute path

    Returns:
        Relative path
    """
    try:
        return os.path.relpath(path)
    except ValueError:
        # If the path is on a different drive, just return the original path
        return path
