"""Bandit security linter integration."""

import json
import os
import subprocess  # nosec B404 - deliberate, shell disabled
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.bandit.bandit_parser import parse_bandit_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for Bandit configuration
BANDIT_DEFAULT_TIMEOUT: int = 30
BANDIT_DEFAULT_PRIORITY: int = 90  # High priority for security tool
BANDIT_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]
BANDIT_OUTPUT_FORMAT: str = "json"


def _extract_bandit_json(raw_text: str) -> dict[str, Any]:
    """Extract Bandit's JSON object from mixed stdout/stderr text.

    Bandit may print informational lines and a progress bar alongside the
    JSON report. This helper locates the first opening brace and the last
    closing brace and attempts to parse the enclosed JSON object.

    Args:
        raw_text: str: Combined stdout+stderr text from Bandit.

    Returns:
        dict[str, Any]: Parsed JSON object.

    Raises:
        JSONDecodeError: If JSON cannot be parsed.
        ValueError: If no JSON object boundaries are found.
    """
    if not raw_text or not raw_text.strip():
        raise json.JSONDecodeError("Empty output", raw_text or "", 0)

    text: str = raw_text.strip()

    # Quick path: if the entire text is JSON
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    start: int = text.find("{")
    end: int = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Could not locate JSON object in Bandit output")

    json_str: str = text[start : end + 1]
    return json.loads(json_str)


def _load_bandit_config() -> dict[str, Any]:
    """Load bandit configuration from pyproject.toml.

    Returns:
        dict[str, Any]: Bandit configuration dictionary.
    """
    config: dict[str, Any] = {}
    pyproject_path = Path("pyproject.toml")

    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "tool" in pyproject_data and "bandit" in pyproject_data["tool"]:
                    config = pyproject_data["tool"]["bandit"]
        except Exception as e:
            logger.warning(f"Failed to load bandit configuration: {e}")

    return config


@dataclass
class BanditTool(BaseTool):
    """Bandit security linter integration.

    Bandit is a security linter designed to find common security issues in Python code.
    It processes Python files, builds an AST, and runs security plugins against the
    AST nodes. Bandit does not support auto-fixing of issues.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "bandit"
    description: str = (
        "Security linter that finds common security issues in Python code"
    )
    can_fix: bool = False  # Bandit does not support auto-fixing
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=BANDIT_DEFAULT_PRIORITY,  # High priority for security
            conflicts_with=[],  # Can work alongside other tools
            file_patterns=BANDIT_FILE_PATTERNS,  # Python files only
            tool_type=ToolType.SECURITY,  # Security-focused tool
            options={
                "timeout": BANDIT_DEFAULT_TIMEOUT,  # Default timeout in seconds
                "severity": None,  # Minimum severity level (LOW, MEDIUM, HIGH)
                "confidence": None,  # Minimum confidence level (LOW, MEDIUM, HIGH)
                "tests": None,  # Comma-separated list of test IDs to run
                "skips": None,  # Comma-separated list of test IDs to skip
                "profile": None,  # Profile to use
                "configfile": None,  # Path to config file
                "baseline": None,  # Path to baseline report for comparison
                "ignore_nosec": False,  # Ignore # nosec comments
                "aggregate": "vuln",  # Aggregate by vulnerability or file
                "verbose": False,  # Verbose output
                "quiet": False,  # Quiet mode
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool with default configuration."""
        super().__post_init__()

        # Load bandit configuration from pyproject.toml
        bandit_config = _load_bandit_config()

        # Apply configuration overrides
        if "exclude_dirs" in bandit_config:
            # Convert exclude_dirs to exclude patterns
            exclude_dirs = bandit_config["exclude_dirs"]
            if isinstance(exclude_dirs, list):
                for exclude_dir in exclude_dirs:
                    pattern = f"{exclude_dir}/**"
                    if pattern not in self.exclude_patterns:
                        self.exclude_patterns.append(pattern)

        # Set other options from configuration
        config_mapping = {
            "tests": "tests",
            "skips": "skips",
            "profile": "profile",
            "configfile": "configfile",
            "baseline": "baseline",
            "ignore_nosec": "ignore_nosec",
            "aggregate": "aggregate",
            # Newly mapped options from pyproject
            "severity": "severity",
            "confidence": "confidence",
        }

        for config_key, option_key in config_mapping.items():
            if config_key in bandit_config:
                self.options[option_key] = bandit_config[config_key]

    def set_options(
        self,
        severity: str | None = None,
        confidence: str | None = None,
        tests: str | None = None,
        skips: str | None = None,
        profile: str | None = None,
        configfile: str | None = None,
        baseline: str | None = None,
        ignore_nosec: bool | None = None,
        aggregate: str | None = None,
        verbose: bool | None = None,
        quiet: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Bandit-specific options.

        Args:
            severity: str | None: Minimum severity level (LOW, MEDIUM, HIGH).
            confidence: str | None: Minimum confidence level (LOW, MEDIUM, HIGH).
            tests: str | None: Comma-separated list of test IDs to run.
            skips: str | None: Comma-separated list of test IDs to skip.
            profile: str | None: Profile to use.
            configfile: str | None: Path to config file.
            baseline: str | None: Path to baseline report for comparison.
            ignore_nosec: bool | None: Ignore # nosec comments.
            aggregate: str | None: Aggregate by vulnerability or file.
            verbose: bool | None: Verbose output.
            quiet: bool | None: Quiet mode.
            **kwargs: Other tool options.

        Raises:
            ValueError: If an option value is invalid.
        """
        # Validate severity level
        if severity is not None:
            valid_severities = ["LOW", "MEDIUM", "HIGH"]
            if severity.upper() not in valid_severities:
                raise ValueError(f"severity must be one of {valid_severities}")
            severity = severity.upper()

        # Validate confidence level
        if confidence is not None:
            valid_confidences = ["LOW", "MEDIUM", "HIGH"]
            if confidence.upper() not in valid_confidences:
                raise ValueError(f"confidence must be one of {valid_confidences}")
            confidence = confidence.upper()

        # Validate aggregate option
        if aggregate is not None:
            valid_aggregates = ["vuln", "file"]
            if aggregate not in valid_aggregates:
                raise ValueError(f"aggregate must be one of {valid_aggregates}")

        options: dict[str, Any] = {
            "severity": severity,
            "confidence": confidence,
            "tests": tests,
            "skips": skips,
            "profile": profile,
            "configfile": configfile,
            "baseline": baseline,
            "ignore_nosec": ignore_nosec,
            "aggregate": aggregate,
            "verbose": verbose,
            "quiet": quiet,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_check_command(
        self,
        files: list[str],
    ) -> list[str]:
        """Build the bandit check command.

        Args:
            files: list[str]: List of files to check.

        Returns:
            list[str]: List of command arguments.
        """
        # Resolve executable via BaseTool preferences to ensure reliable
        # execution inside the active environment (prefers 'uv run bandit' when
        # available), falling back to a direct executable.
        exec_cmd: list[str] = self._get_executable_command("bandit")

        cmd: list[str] = exec_cmd + ["-r"]

        # Add configuration options
        if self.options.get("severity"):
            severity = self.options["severity"]
            if severity == "LOW":
                cmd.append("-l")
            elif severity == "MEDIUM":
                cmd.extend(["-ll"])
            elif severity == "HIGH":
                cmd.extend(["-lll"])

        if self.options.get("confidence"):
            confidence = self.options["confidence"]
            if confidence == "LOW":
                cmd.append("-i")
            elif confidence == "MEDIUM":
                cmd.extend(["-ii"])
            elif confidence == "HIGH":
                cmd.extend(["-iii"])

        if self.options.get("tests"):
            cmd.extend(["-t", self.options["tests"]])

        if self.options.get("skips"):
            cmd.extend(["-s", self.options["skips"]])

        if self.options.get("profile"):
            cmd.extend(["-p", self.options["profile"]])

        if self.options.get("configfile"):
            cmd.extend(["-c", self.options["configfile"]])

        if self.options.get("baseline"):
            cmd.extend(["-b", self.options["baseline"]])

        if self.options.get("ignore_nosec"):
            cmd.append("--ignore-nosec")

        if self.options.get("aggregate"):
            cmd.extend(["-a", self.options["aggregate"]])

        if self.options.get("verbose"):
            cmd.append("-v")

        if self.options.get("quiet"):
            cmd.append("-q")

        # Output format
        cmd.extend(["-f", BANDIT_OUTPUT_FORMAT])

        # Add quiet flag (once) to suppress log messages that interfere with JSON
        # parsing. Guard against duplicates when quiet=True already added it.
        if "-q" not in cmd:
            cmd.append("-q")

        # Add files
        cmd.extend(files)

        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Bandit for security issues.

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not python_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Python files found to check.",
                issues_count=0,
            )

        logger.debug(f"Files to check: {python_files}")

        # Ensure Bandit discovers the correct configuration by setting the
        # working directory to the common parent of the target files.
        cwd: str | None = self.get_cwd(paths=python_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in python_files
        ]

        timeout: int = self.options.get("timeout", BANDIT_DEFAULT_TIMEOUT)
        cmd: list[str] = self._build_check_command(files=rel_files)

        output: str
        execution_failure: bool = False
        # Run Bandit via the shared safe runner in BaseTool. This enforces
        # argument validation and consistent subprocess handling across tools.
        try:
            success, combined = self._run_subprocess(
                cmd=cmd,
                timeout=timeout,
                cwd=cwd,
            )
            output = (combined or "").strip()
            rc: int = 0 if success else 1
        except subprocess.TimeoutExpired:
            # Handle timeout gracefully
            execution_failure = True
            timeout_msg = (
                f"Bandit execution timed out ({timeout}s limit exceeded).\n\n"
                "This may indicate:\n"
                "  - Large codebase taking too long to process\n"
                "  - Need to increase timeout via --tool-options bandit:timeout=N"
            )
            output = timeout_msg
            rc = 1
        except Exception as e:
            logger.error(f"Failed to run Bandit: {e}")
            output = f"Bandit failed: {e}"
            execution_failure = True
            rc = 1

        # Parse the JSON output
        try:
            # If command failed and no obvious JSON present, surface error cleanly
            if (
                ("{" not in output or "}" not in output)
                and "rc" in locals()
                and rc != 0
            ):
                return ToolResult(
                    name=self.name,
                    success=False,
                    output=output,
                    issues_count=0,
                )

            # Attempt robust JSON extraction from mixed output
            bandit_data = _extract_bandit_json(raw_text=output)
            issues = parse_bandit_output(bandit_data)
            issues_count = len(issues)

            # Bandit returns 0 if no issues; 1 if issues found (still successful run)
            execution_success = (
                len(bandit_data.get("errors", [])) == 0 and not execution_failure
            )

            return ToolResult(
                name=self.name,
                success=execution_success,
                output=output if execution_failure else None,
                issues_count=issues_count,
                issues=issues,
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse bandit output: {e}")
            return ToolResult(
                name=self.name,
                success=False,
                output=(output or f"Failed to parse bandit output: {str(e)}"),
                issues_count=0,
            )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files with Bandit.

        Note: Bandit does not support auto-fixing of security issues.
        This method raises NotImplementedError.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Raises:
            NotImplementedError: Always raised since Bandit doesn't support fixing.
        """
        # Bandit cannot auto-fix issues; explicitly signal this.
        raise NotImplementedError("Bandit does not support auto-fixing.")
