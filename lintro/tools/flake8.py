"""Flake8 linter integration."""

import re
import subprocess

from lintro.tools import Tool, ToolConfig


class Flake8Tool(Tool):
    """Flake8 linter integration."""

    name = "flake8"
    description = "Python linter that checks for style and logical errors"
    can_fix = False  # Flake8 can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=50,  # Lower priority than formatters
        conflicts_with=[],  # No direct conflicts, but should run after formatters
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
        """Check files with Flake8."""
        # Base command
        cmd = ["flake8"]

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
            cmd.extend(["--exclude", ",".join(exclude_patterns)])

        # Add paths
        cmd.extend(paths)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "No style issues found."
        except subprocess.CalledProcessError as e:
            # Flake8 returns exit code 1 when it finds style issues
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
        """Flake8 cannot fix issues, only report them."""
        return (
            False,
            "Flake8 cannot automatically fix issues. Run 'lintro check' to see issues.",
        )
