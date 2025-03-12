"""Pylint linter integration."""

import re
import subprocess

from lintro.tools import Tool, ToolConfig


class PylintTool(Tool):
    """Pylint linter integration."""

    name = "pylint"
    description = "Python linter that checks for errors, enforces coding standards, and looks for code smells"
    can_fix = False  # Pylint can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=45,  # Lower priority than formatters, higher than flake8
        conflicts_with=[],  # No direct conflicts, but should run after formatters
        file_patterns=["*.py"],  # Only applies to Python files
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.rcfile = None

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        rcfile: str | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            rcfile: Path to pylint configuration file
        """
        super().set_options(exclude_patterns, include_venv)
        self.rcfile = rcfile

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check files with Pylint.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["pylint"]

        # Add format option for consistent output
        cmd.extend(["--output-format=text"])

        # Add rcfile if specified
        if self.rcfile:
            cmd.extend(["--rcfile", self.rcfile])

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
            cmd.extend(["--ignore=" + ",".join(exclude_patterns)])

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Pylint returns non-zero exit codes for various levels of issues
            # 0 means no error, 1-31 indicate different types of issues
            if result.returncode == 0:
                return True, "No issues found."
            else:
                # Process the output to make it more readable
                output = result.stdout or result.stderr

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
        except subprocess.CalledProcessError as e:
            # This should only happen if pylint itself crashes
            return False, f"Error running pylint: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return False, "Pylint not found. Please install it with 'pip install pylint'."

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Pylint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as pylint cannot fix issues
            - output: Message indicating pylint cannot fix issues
        """
        return (
            False,
            "Pylint cannot automatically fix issues. Run 'lintro check' to see issues.",
        ) 