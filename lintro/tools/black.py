"""Black code formatter integration."""

import re
import subprocess

from lintro.tools import Tool, ToolConfig


class BlackTool(Tool):
    """Black code formatter integration."""

    name = "black"
    description = "The uncompromising Python code formatter"
    can_fix = True

    # Configure tool with conflict information
    config = ToolConfig(
        priority=100,  # High priority as Black is an opinionated formatter
        conflicts_with=["autopep8", "yapf"],  # Conflicts with other formatters
        file_patterns=["*.py"],  # Only applies to Python files
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """Check if files would be reformatted by Black."""
        # Base command
        cmd = ["black", "--check"]

        # Add exclude patterns
        exclude_patterns = self.exclude_patterns.copy()

        # Add virtual environment patterns if not explicitly included
        if not self.include_venv:
            venv_patterns = [
                r"\.venv",
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
            cmd.extend(["--exclude", "|".join(exclude_patterns)])

        # Add paths
        cmd.extend(paths)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "All files would be left unchanged."
        except subprocess.CalledProcessError as e:
            # Black returns exit code 1 when it would reformat files
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
        """Format files with Black."""
        # Base command
        cmd = ["black"]

        # Add exclude patterns
        exclude_patterns = self.exclude_patterns.copy()

        # Add virtual environment patterns if not explicitly included
        if not self.include_venv:
            venv_patterns = [
                r"\.venv",
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
            cmd.extend(["--exclude", "|".join(exclude_patterns)])

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, result.stdout or "All files formatted successfully."
        except subprocess.CalledProcessError as e:
            return False, e.stderr or "Failed to format files with Black."
