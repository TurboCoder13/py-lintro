"""YAMLLint linter integration."""

import os
import re
import subprocess
from pathlib import Path

from lintro.tools import Tool, ToolConfig


class YAMLLintTool(Tool):
    """YAMLLint linter integration."""

    name = "yamllint"
    description = "Linter for YAML files"
    can_fix = False  # YAMLLint can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=45,  # Similar priority to other linters
        conflicts_with=[],  # No direct conflicts
        file_patterns=["*.yaml", "*.yml"],  # YAML files
        options={
            "config_file": None,  # Default to None (use default yamllint config)
            "strict": False,  # Default to non-strict mode
        },
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.config_file = self.config.options.get("config_file")
        self.strict = self.config.options.get("strict", False)

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        config_file: str | None = None,
        strict: bool | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            config_file: Path to yamllint configuration file
            strict: Whether to use strict mode
        """
        super().set_options(exclude_patterns, include_venv)
        if config_file is not None:
            self.config_file = config_file
        if strict is not None:
            self.strict = strict

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check YAML files with yamllint.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["yamllint", "-f", "parsable"]

        # Add strict mode if enabled
        if self.strict:
            cmd.append("-s")

        # Add config file if specified
        if self.config_file:
            cmd.extend(["-c", self.config_file])

        # Add exclude patterns
        exclude_patterns = self.exclude_patterns.copy()

        # Add virtual environment patterns if not explicitly included
        if not self.include_venv:
            venv_patterns = [
                ".venv",
                "venv",
                "env",
                "ENV",
                "virtualenv",
                "virtual_env",
                "virtualenvs",
                "site-packages",
            ]
            exclude_patterns.extend(venv_patterns)

        # Process each path to find YAML files
        yaml_files = []
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith((".yaml", ".yml")):
                            file_path = os.path.join(root, file)
                            # Skip files in excluded patterns
                            if not self._should_exclude(file_path, exclude_patterns):
                                yaml_files.append(file_path)
            elif path.endswith((".yaml", ".yml")):
                if not self._should_exclude(path, exclude_patterns):
                    yaml_files.append(path)

        if not yaml_files:
            return True, "No YAML files found in the specified paths."

        # Add paths
        cmd.extend(yaml_files)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # If return code is 0, no issues were found
            if result.returncode == 0:
                return True, "No YAML issues found."
            
            # If return code is not 0 but there's no stderr, there are linting issues
            if result.returncode != 0 and not result.stderr:
                return False, result.stdout
            
            # If there's stderr, there was an error running yamllint
            return False, result.stderr or "Error running yamllint."
                
        except subprocess.CalledProcessError as e:
            return False, f"Error running yamllint: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return False, "yamllint not found. Please install it with 'pip install yamllint'."

    def _should_exclude(self, file_path: str, exclude_patterns: list[str]) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Args:
            file_path: Path to the file
            exclude_patterns: List of patterns to exclude

        Returns:
            True if the file should be excluded, False otherwise
        """
        for pattern in exclude_patterns:
            if pattern in file_path:
                return True
        return False

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        YAMLLint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as yamllint cannot fix issues
            - output: Message indicating yamllint cannot fix issues
        """
        return (
            False,
            "YAMLLint cannot automatically fix issues. Run 'lintro check' to see issues.",
        ) 