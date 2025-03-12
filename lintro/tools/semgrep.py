"""Semgrep static analysis integration."""

import json
import re
import subprocess
from typing import Any

from lintro.tools import Tool, ToolConfig


class SemgrepTool(Tool):
    """Semgrep static analysis integration."""

    name = "semgrep"
    description = "Static analysis tool for finding bugs and security issues in code"
    can_fix = False  # Semgrep can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=40,  # Lower priority than formatters, similar to other linters
        conflicts_with=[],  # No direct conflicts
        file_patterns=["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.rb"],  # Supports many languages
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.config_option = "auto"  # Default to auto configuration

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        config_option: str | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            config_option: Semgrep configuration option (e.g., 'auto', 'p/python')
        """
        super().set_options(exclude_patterns, include_venv)
        if config_option:
            self.config_option = config_option

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check files with Semgrep.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Base command - use text output instead of JSON
        cmd = ["semgrep", "scan"]

        # Add configuration
        cmd.extend(["--config", self.config_option])

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

        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Process the output
            output = result.stdout
            
            # Check if there are findings
            has_findings = "Code Findings" in output and not "0 Code Findings" in output
            
            # Extract the findings section
            if has_findings:
                # Try a simpler approach: extract everything between the findings header and the summary header
                lines = output.splitlines()
                
                # Find the line with "Code Findings"
                findings_start = -1
                for i, line in enumerate(lines):
                    if "Code Findings" in line:
                        findings_start = i
                        break
                
                if findings_start >= 0:
                    # Skip the header box (3 lines) and extract the findings
                    findings_lines = []
                    for i in range(findings_start + 3, len(lines)):
                        if "Scan Summary" in lines[i]:
                            break
                        findings_lines.append(lines[i])
                    
                    findings_section = "\n".join(findings_lines)
                    return False, findings_section
            
            # If no findings or extraction failed, return success
            return True, "No issues found."
                
        except subprocess.CalledProcessError as e:
            return False, f"Error running semgrep: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return False, "Semgrep not found. Please install it with 'pip install semgrep'."

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Semgrep cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as semgrep cannot fix issues
            - output: Message indicating semgrep cannot fix issues
        """
        return (
            False,
            "Semgrep cannot automatically fix issues. Run 'lintro check' to see issues.",
        ) 