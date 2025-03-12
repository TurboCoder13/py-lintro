"""isort import sorter integration."""

import re
import subprocess

from lintro.tools import Tool


class IsortTool(Tool):
    """isort import sorter integration."""

    name = "isort"
    description = "Sort Python imports"
    can_fix = True

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """Check if imports would be sorted by isort."""
        # Base command
        cmd = ["isort", "--check-only"]

        # Add skip patterns
        skip_patterns = self.exclude_patterns.copy()

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
            skip_patterns.extend(venv_patterns)

        # Add skip patterns to command
        for pattern in skip_patterns:
            cmd.extend(["--skip", pattern])

        # Add paths
        cmd.extend(paths)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "All imports are correctly sorted."
        except subprocess.CalledProcessError as e:
            # isort returns exit code 1 when it would sort imports
            output = e.stdout or e.stderr

            # Filter out lines from virtual environments if not explicitly included
            if not self.include_venv and output:
                filtered_lines = []
                venv_pattern = re.compile(
                    r"(\.venv|venv|env|ENV|virtualenv|virtual_env|virtualenvs|site-packages)"
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
        """Sort imports with isort."""
        # Base command
        cmd = ["isort"]

        # Add skip patterns
        skip_patterns = self.exclude_patterns.copy()

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
            skip_patterns.extend(venv_patterns)

        # Add skip patterns to command
        for pattern in skip_patterns:
            cmd.extend(["--skip", pattern])

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, result.stdout or "All imports sorted successfully."
        except subprocess.CalledProcessError as e:
            return False, e.stderr or "Failed to sort imports with isort."
