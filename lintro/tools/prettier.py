"""Prettier code formatter integration."""

import os
import re
import subprocess
import time
from pathlib import Path

from lintro.tools import Tool, ToolConfig


class PrettierTool(Tool):
    """Prettier code formatter integration."""

    name = "prettier"
    description = "Code formatter that supports multiple languages (JavaScript, TypeScript, CSS, HTML, etc.)"
    can_fix = True  # Prettier can both check and fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=80,  # High priority, similar to black
        conflicts_with=[],  # No direct conflicts
        file_patterns=[
            "*.js", "*.jsx", "*.ts", "*.tsx", "*.css", "*.scss", "*.less", 
            "*.html", "*.json", "*.yaml", "*.yml", "*.md", "*.graphql", "*.vue"
        ],  # Applies to many file types
        options={
            "timeout": 30,  # Default timeout in seconds per file
        },
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.timeout = self.config.options.get("timeout", 30)

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
        """
        self.exclude_patterns = exclude_patterns or []
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check files with Prettier.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["npx", "prettier", "--check"]
        
        # Add paths
        cmd.extend(paths)
        
        try:
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=self.timeout
            )
            return True, "All files are formatted correctly."
        except subprocess.CalledProcessError as e:
            # Prettier returns exit code 1 when it finds formatting issues
            output = e.stdout or e.stderr
            
            # Filter out lines from virtual environments if not explicitly included
            if not self.include_venv and output:
                filtered_lines = []
                venv_pattern = re.compile(
                    r"(\.venv|venv|env|ENV|virtualenv|virtual_env|"
                    r"virtualenvs|site-packages|node_modules)"
                )
                
                for line in output.splitlines():
                    if not venv_pattern.search(line):
                        filtered_lines.append(line)
                
                output = "\n".join(filtered_lines)
            
            return False, output
        except subprocess.TimeoutExpired:
            return False, f"Prettier check timed out after {self.timeout} seconds."
        except Exception as e:
            return False, f"Error running Prettier: {str(e)}"

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Fix files with Prettier.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: True if fixes were applied successfully, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["npx", "prettier", "--write"]
        
        # Add paths
        cmd.extend(paths)
        
        try:
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=self.timeout
            )
            return True, "All files formatted successfully."
        except subprocess.CalledProcessError as e:
            # Prettier might return a non-zero exit code if there are issues
            output = e.stdout or e.stderr
            return False, f"Error formatting files: {output}"
        except subprocess.TimeoutExpired:
            return False, f"Prettier formatting timed out after {self.timeout} seconds."
        except Exception as e:
            return False, f"Error running Prettier: {str(e)}" 