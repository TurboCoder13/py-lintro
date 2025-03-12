"""Hadolint Dockerfile linter integration."""

import re
import subprocess

from lintro.tools import Tool, ToolConfig


class HadolintTool(Tool):
    """Hadolint Dockerfile linter integration."""

    name = "hadolint"
    description = "Dockerfile linter that checks for best practices and common mistakes"
    can_fix = False  # Hadolint can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=45,  # Similar priority to other linters
        conflicts_with=[],  # No direct conflicts
        file_patterns=["Dockerfile*", "*.dockerfile", "*.Dockerfile"],  # Only applies to Dockerfiles
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check Dockerfiles with Hadolint.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["hadolint"]

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "No Dockerfile issues found."
        except subprocess.CalledProcessError as e:
            # Hadolint returns exit code 1 when it finds issues
            output = e.stdout or e.stderr

            # Filter out lines from virtual environments if not explicitly included
            if not self.include_venv and output:
                filtered_lines = []
                venv_pattern = re.compile(
                    r"(\.venv|venv|env|ENV|virtualenv|virtual_env|"
                    r"virtualenvs|site-packages)"
                )

                for line in output.splitlines():
                    if not venv_pattern.search(line):
                        filtered_lines.append(line)

                output = "\n".join(filtered_lines)

            return False, output

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Hadolint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as Hadolint cannot fix issues
            - output: Message indicating that Hadolint cannot fix issues
        """
        return (
            False,
            "Hadolint cannot automatically fix issues. Run 'lintro check' to see issues.",
        ) 