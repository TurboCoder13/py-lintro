"""Pytest test runner integration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.parsers.pytest.pytest_parser import parse_pytest_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for pytest configuration
PYTEST_DEFAULT_TIMEOUT: int = 300  # 5 minutes for test runs
PYTEST_DEFAULT_PRIORITY: int = 90
PYTEST_FILE_PATTERNS: list[str] = ["test_*.py", "*_test.py"]
PYTEST_OUTPUT_FORMAT: str = "text"
PYTEST_TEST_MODE_ENV: str = "LINTRO_TEST_MODE"
PYTEST_TEST_MODE_VALUE: str = "1"


def _load_pytest_config() -> dict:
    """Load pytest configuration from pyproject.toml or pytest.ini.

    Returns:
        dict: Pytest configuration dictionary.
    """
    config: dict = {}
    
    # Check pyproject.toml first
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "tool" in pyproject_data and "pytest" in pyproject_data["tool"]:
                    config = pyproject_data["tool"]["pytest"]
        except Exception as e:
            logger.warning(f"Failed to load pytest configuration from pyproject.toml: {e}")
    
    # Check pytest.ini
    pytest_ini_path = Path("pytest.ini")
    if pytest_ini_path.exists():
        try:
            import configparser
            parser = configparser.ConfigParser()
            parser.read(pytest_ini_path)
            if "pytest" in parser:
                config.update(dict(parser["pytest"]))
        except Exception as e:
            logger.warning(f"Failed to load pytest configuration from pytest.ini: {e}")

    return config


def _load_lintro_ignore() -> list[str]:
    """Load ignore patterns from .lintro-ignore file.

    Returns:
        list[str]: List of ignore patterns.
    """
    ignore_patterns: list[str] = []
    ignore_file = Path(".lintro-ignore")

    if ignore_file.exists():
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception as e:
            logger.warning(f"Failed to load .lintro-ignore: {e}")

    return ignore_patterns


@dataclass
class PytestTool(BaseTool):
    """Pytest test runner integration.

    Pytest is a mature full-featured Python testing tool that helps you write
    better programs. It supports various testing patterns and provides extensive
    configuration options.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "pytest"
    description: str = (
        "Mature full-featured Python testing tool that helps you write better programs"
    )
    can_fix: bool = False  # pytest doesn't fix code, it runs tests
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=PYTEST_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=PYTEST_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
        ),
    )
    exclude_patterns: list[str] = field(default_factory=_load_lintro_ignore)
    include_venv: bool = False
    _default_timeout: int = PYTEST_DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        """Initialize the tool after dataclass creation."""
        super().__post_init__()
        
        # Load pytest configuration
        pytest_config = _load_pytest_config()
        
        # Set default options based on configuration
        default_options = {
            "verbose": True,
            "tb": "short",  # Traceback format
            "maxfail": 1,   # Stop after first failure
            "no_header": True,
            "disable_warnings": True,
        }
        
        # Override with config file settings
        if pytest_config:
            if "addopts" in pytest_config:
                # Parse addopts string
                addopts = pytest_config["addopts"].split()
                for opt in addopts:
                    if opt.startswith("--"):
                        key = opt[2:].replace("-", "_")
                        default_options[key] = True
                    elif opt.startswith("-"):
                        key = opt[1:].replace("-", "_")
                        default_options[key] = True
        
        self.options.update(default_options)

    def set_options(
        self,
        verbose: bool | None = None,
        tb: str | None = None,
        maxfail: int | None = None,
        no_header: bool | None = None,
        disable_warnings: bool | None = None,
        json_report: bool | None = None,
        junitxml: str | None = None,
        **kwargs,
    ) -> None:
        """Set pytest-specific options.

        Args:
            verbose: Enable verbose output.
            tb: Traceback format (short, long, auto, line, native).
            maxfail: Stop after first N failures.
            no_header: Disable header.
            disable_warnings: Disable warnings.
            json_report: Enable JSON report output.
            junitxml: Path for JUnit XML output.
            **kwargs: Additional options.
        """
        if verbose is not None and not isinstance(verbose, bool):
            raise ValueError("verbose must be a boolean")

        if tb is not None and tb not in ("short", "long", "auto", "line", "native"):
            raise ValueError("tb must be one of: short, long, auto, line, native")

        if maxfail is not None and not isinstance(maxfail, int):
            raise ValueError("maxfail must be an integer")

        if no_header is not None and not isinstance(no_header, bool):
            raise ValueError("no_header must be a boolean")

        if disable_warnings is not None and not isinstance(disable_warnings, bool):
            raise ValueError("disable_warnings must be a boolean")

        if json_report is not None and not isinstance(json_report, bool):
            raise ValueError("json_report must be a boolean")

        if junitxml is not None and not isinstance(junitxml, str):
            raise ValueError("junitxml must be a string")

        options: dict = {
            "verbose": verbose,
            "tb": tb,
            "maxfail": maxfail,
            "no_header": no_header,
            "disable_warnings": disable_warnings,
            "json_report": json_report,
            "junitxml": junitxml,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_check_command(
        self,
        files: list[str],
        fix: bool = False,
    ) -> list[str]:
        """Build the pytest command.

        Args:
            files: list[str]: List of files to test.
            fix: bool: Ignored for pytest (not applicable).

        Returns:
            list[str]: List of command arguments.
        """
        cmd: list[str] = self._get_executable_command(tool_name="pytest")

        # Add verbosity
        if self.options.get("verbose", True):
            cmd.append("-v")

        # Add traceback format
        tb_format = self.options.get("tb", "short")
        cmd.extend(["--tb", tb_format])

        # Add maxfail
        maxfail = self.options.get("maxfail", 1)
        cmd.extend(["--maxfail", str(maxfail)])

        # Add no-header
        if self.options.get("no_header", True):
            cmd.append("--no-header")

        # Add disable-warnings
        if self.options.get("disable_warnings", True):
            cmd.append("--disable-warnings")

        # Add output format options
        if self.options.get("json_report", False):
            cmd.append("--json-report")
            cmd.append("--json-report-file=pytest-report.json")

        if self.options.get("junitxml"):
            cmd.extend(["--junitxml", self.options["junitxml"]])

        # Add test mode isolation if in test mode
        if os.environ.get(PYTEST_TEST_MODE_ENV) == PYTEST_TEST_MODE_VALUE:
            cmd.append("--strict-markers")
            cmd.append("--strict-config")

        # Add files
        cmd.extend(files)

        return cmd

    def _parse_output(
        self,
        output: str,
        return_code: int,
    ) -> list[PytestIssue]:
        """Parse pytest output into issues.

        Args:
            output: Raw output from pytest.
            return_code: Return code from pytest.

        Returns:
            list[PytestIssue]: Parsed test failures and errors.
        """
        # Determine output format
        output_format = "text"
        if self.options.get("json_report", False):
            output_format = "json"
        elif self.options.get("junitxml"):
            output_format = "junit"

        # Parse based on format
        issues = parse_pytest_output(output, format=output_format)

        # If no issues found but return code indicates failure, try text parsing
        if not issues and return_code != 0:
            issues = parse_pytest_output(output, format="text")

        return issues

    def check(
        self,
        files: list[str] | None = None,
        paths: list[str] | None = None,
        fix: bool = False,
    ) -> ToolResult:
        """Run pytest on specified files.

        Args:
            files: list[str] | None: Files to test. If None, uses file patterns.
            paths: list[str] | None: Paths to test. If None, uses file patterns.
            fix: bool: Ignored for pytest.

        Returns:
            ToolResult: Results from pytest execution.
        """
        # Use paths if provided, otherwise files, otherwise discover files
        target_files = paths or files
        if target_files is None:
            target_files = walk_files_with_excludes(
                paths=["."],
                file_patterns=self.config.file_patterns,
                exclude_patterns=self.exclude_patterns,
                include_venv=self.include_venv,
            )

        if not target_files:
            return ToolResult(
                name=self.name,
                success=True,
                issues=[],
                output="No test files found.",
            )

        cmd = self._build_check_command(target_files, fix)
        
        try:
            success, output = self._run_subprocess(cmd)
            issues = self._parse_output(output, 0 if success else 1)
            
            return ToolResult(
                name=self.name,
                success=success,
                issues=issues,
                output=output,
            )
        except Exception as e:
            logger.error(f"Error running pytest: {e}")
            return ToolResult(
                name=self.name,
                success=False,
                issues=[],
                output=f"Error: {e}",
            )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files.

        Args:
            paths: list[str]: List of file paths to fix.

        Raises:
            NotImplementedError: pytest does not support fixing issues.
        """
        if not self.can_fix:
            raise NotImplementedError(f"{self.name} does not support fixing issues")
        
        # pytest doesn't fix code, it runs tests
        raise NotImplementedError("pytest does not support fixing issues - it only runs tests")
