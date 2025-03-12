"""Hadolint Dockerfile linter integration."""

import os
import subprocess
import shutil
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
        # Only applies to Dockerfiles
        file_patterns=[
            "Dockerfile*",
            "*.dockerfile",
            "*.Dockerfile"
        ],
        options={
            "timeout": 10,  # Default timeout in seconds per file
        },
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        # Get timeout from config or use default
        self.timeout = self.config.options.get("timeout", 10)
        self._check_hadolint_available()

    def _check_hadolint_available(self):
        """Check if hadolint is available in the PATH."""
        self.hadolint_available = shutil.which("hadolint") is not None

    def set_options(
        self,
        exclude_patterns=None,
        include_venv=False,
        timeout=None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 10)
        """
        super().set_options(exclude_patterns, include_venv)
        if timeout is not None:
            self.timeout = timeout

    def check(
        self,
        paths,
    ):
        """
        Check Dockerfiles with Hadolint.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # Check if hadolint is available
        if not self.hadolint_available:
            return False, (
                "Hadolint binary not found in PATH. "
                "Please install hadolint or use the Docker version of lintro."
            )

        # Process each file individually to prevent hanging on large codebases
        all_outputs = []
        success = True
        skipped_files = []
        processed_files = 0

        # Expand directories to individual Dockerfile files
        dockerfile_files = []
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        dockerfile_match = (
                            file == "Dockerfile" or
                            file.startswith("Dockerfile.") or
                            file.endswith(".dockerfile") or
                            file.endswith(".Dockerfile")
                        )
                        if dockerfile_match:
                            file_path = os.path.join(root, file)
                            # Skip files in excluded patterns
                            if not self._should_exclude(file_path):
                                dockerfile_files.append(file_path)
            elif os.path.isfile(path) and (
                    path.endswith("Dockerfile") or
                    path.startswith("Dockerfile.") or
                    path.endswith(".dockerfile") or
                    path.endswith(".Dockerfile")):
                if not self._should_exclude(path):
                    dockerfile_files.append(path)

        if not dockerfile_files:
            return True, "No Dockerfile files found in the specified paths."

        # Process each file with a timeout
        for file_path in dockerfile_files:
            processed_files += 1
            try:
                # Base command for a single file
                cmd = ["hadolint", file_path]

                # Run with timeout
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                        check=False,
                    )
                    
                    if result.returncode == 0:
                        # No issues found in this file
                        pass
                    else:
                        # Issues found
                        success = False
                        output = result.stdout or result.stderr
                        if output:
                            all_outputs.append(output)
                except subprocess.TimeoutExpired:
                    skipped_files.append(file_path)
                    success = False  # Mark as failed if any file times out
                    timeout_msg = f"Skipped {file_path} (timeout after {self.timeout}s)"
                    all_outputs.append(timeout_msg)
            except Exception as e:
                skipped_files.append(file_path)
                success = False  # Mark as failed if any file has an error
                error_msg = f"Error processing {file_path}: {str(e)}"
                all_outputs.append(error_msg)

        # Prepare the final output
        if not all_outputs:
            return True, "No Dockerfile issues found."
        else:
            output = "\n".join(all_outputs)
            if skipped_files:
                skip_count = len(skipped_files)
                skip_msg = f"\n\nSkipped {skip_count} files due to timeout or errors."
                output += skip_msg
            return success, output

    def _should_exclude(self, file_path):
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
        paths,
    ):
        """
        Hadolint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: False as Hadolint cannot fix issues
            - output: Message indicating that Hadolint cannot fix issues
        """
        msg = "Hadolint cannot automatically fix issues. Run lintro check"
        return (False, msg)
