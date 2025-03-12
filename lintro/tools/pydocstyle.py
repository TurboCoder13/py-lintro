"""Pydocstyle docstring style checker integration."""

import os
import re
import subprocess
import time
from pathlib import Path

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
                # Base command for a single file
                cmd = ["pydocstyle", "--convention", self.convention, file_path]
                
                # Run with timeout
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
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
                            all_outputs.append(output)
                except subprocess.TimeoutExpired:
                    process.kill()
                    skipped_files.append(file_path)
                    all_success = False  # Mark as failed if any file times out
                    all_outputs.append(f"Skipped {file_path} (timeout after {self.timeout}s)")
            except Exception as e:
                skipped_files.append(file_path)
                all_success = False  # Mark as failed if any file has an error
                all_outputs.append(f"Error processing {file_path}: {str(e)}")
        
        # Prepare the final output
        if not all_outputs:
            return True, "No docstring style issues found."
        else:
            output = "\n".join(all_outputs)
            if skipped_files:
                output += f"\n\nSkipped {len(skipped_files)} files due to timeout or errors."
            return all_success, output

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
            venv_patterns = [
                ".venv", "venv", "env", "ENV", "virtualenv", 
                "virtual_env", "virtualenvs", "site-packages"
            ]
            for pattern in venv_patterns:
                if pattern in file_path:
                    return True
        
        # Check user-defined exclusion patterns
        for pattern in self.exclude_patterns:
            if pattern in file_path:
                return True
        
        return False

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Pydocstyle cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as Pydocstyle cannot fix issues
            - output: Message indicating that Pydocstyle cannot fix issues
        """
        return (
            False,
            "Pydocstyle cannot automatically fix issues. Run 'lintro check' to see issues.",
        ) 