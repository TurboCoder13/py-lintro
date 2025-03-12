"""MyPy type checker integration."""

import re
import subprocess

from lintro.tools import Tool, ToolConfig


class MypyTool(Tool):
    """MyPy static type checker integration."""

    name = "mypy"
    description = "Static type checker for Python"
    can_fix = False  # MyPy can only check, not fix

    # Configure tool with conflict information
    config = ToolConfig(
        priority=50,  # Lower priority than formatters
        conflicts_with=[],  # No direct conflicts, but should run after formatters
        file_patterns=["*.py"],  # Only applies to Python files
    )

    def __init__(self) -> None:
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.config_file = None
        self.python_version = None
        self.disallow_untyped_defs = None
        self.disallow_incomplete_defs = None
        self.check_untyped_defs = None
        self.warn_return_any = None
        self.warn_unused_ignores = None
        self.warn_redundant_casts = None
        self.no_implicit_optional = None
        self.strict_optional = None

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """Check files with MyPy."""
        # Base command
        cmd = ["mypy"]

        # Add configuration file if specified
        if self.config_file:
            cmd.extend(["--config-file", self.config_file])

        # Add Python version if specified
        if self.python_version:
            cmd.extend(["--python-version", self.python_version])

        # Add type checking options if specified
        if self.disallow_untyped_defs is not None:
            if self.disallow_untyped_defs:
                cmd.append("--disallow-untyped-defs")
            else:
                cmd.append("--no-disallow-untyped-defs")

        if self.disallow_incomplete_defs is not None:
            if self.disallow_incomplete_defs:
                cmd.append("--disallow-incomplete-defs")
            else:
                cmd.append("--no-disallow-incomplete-defs")

        if self.check_untyped_defs is not None:
            if self.check_untyped_defs:
                cmd.append("--check-untyped-defs")
            else:
                cmd.append("--no-check-untyped-defs")

        if self.warn_return_any is not None:
            if self.warn_return_any:
                cmd.append("--warn-return-any")
            else:
                cmd.append("--no-warn-return-any")

        if self.warn_unused_ignores is not None:
            if self.warn_unused_ignores:
                cmd.append("--warn-unused-ignores")
            else:
                cmd.append("--no-warn-unused-ignores")

        if self.warn_redundant_casts is not None:
            if self.warn_redundant_casts:
                cmd.append("--warn-redundant-casts")
            else:
                cmd.append("--no-warn-redundant-casts")

        if self.no_implicit_optional is not None:
            if self.no_implicit_optional:
                cmd.append("--no-implicit-optional")
            else:
                cmd.append("--implicit-optional")

        if self.strict_optional is not None:
            if self.strict_optional:
                cmd.append("--strict-optional")
            else:
                cmd.append("--no-strict-optional")

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
            for pattern in venv_patterns:
                cmd.extend(["--exclude", pattern])

        # Add paths
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "No type issues found."
        except subprocess.CalledProcessError as e:
            # MyPy returns exit code 1 when it finds type issues
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
        """MyPy cannot fix issues, only report them."""
        return (
            False,
            "MyPy cannot automatically fix issues. Run 'lintro check' to see issues.",
        )

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        config_file: str | None = None,
        python_version: str | None = None,
        disallow_untyped_defs: bool | None = None,
        disallow_incomplete_defs: bool | None = None,
        check_untyped_defs: bool | None = None,
        warn_return_any: bool | None = None,
        warn_unused_ignores: bool | None = None,
        warn_redundant_casts: bool | None = None,
        no_implicit_optional: bool | None = None,
        strict_optional: bool | None = None,
    ) -> None:
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            config_file: Path to mypy configuration file
            python_version: Python version to use for type checking
            disallow_untyped_defs: Whether to disallow untyped function definitions
            disallow_incomplete_defs: Whether to disallow incomplete function definitions
            check_untyped_defs: Whether to check the body of untyped functions
            warn_return_any: Whether to warn when returning Any from a function
            warn_unused_ignores: Whether to warn about unused # type: ignore comments
            warn_redundant_casts: Whether to warn about redundant casts
            no_implicit_optional: Whether to disallow implicit Optional types
            strict_optional: Whether to enable strict Optional checking
        """
        super().set_options(exclude_patterns, include_venv)
        self.config_file = config_file
        self.python_version = python_version
        self.disallow_untyped_defs = disallow_untyped_defs
        self.disallow_incomplete_defs = disallow_incomplete_defs
        self.check_untyped_defs = check_untyped_defs
        self.warn_return_any = warn_return_any
        self.warn_unused_ignores = warn_unused_ignores
        self.warn_redundant_casts = warn_redundant_casts
        self.no_implicit_optional = no_implicit_optional
        self.strict_optional = strict_optional
