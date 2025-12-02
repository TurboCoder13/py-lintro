"""Utility functions for pytest tool implementation.

This module contains helper functions extracted from tool_pytest.py to improve
maintainability and reduce file size. Functions are organized by category:
- JUnit XML processing
- Environment and system utilities
- Flaky test detection
- Configuration loading
- Plugin management
"""

import json
import os
import shlex
import subprocess  # nosec B404 - used safely with shell disabled
from pathlib import Path

from loguru import logger

from lintro.parsers.pytest.pytest_issue import PytestIssue

# Constants for flaky test detection
PYTEST_FLAKY_CACHE_FILE: str = ".pytest_cache/lintro_flaky_tests.json"
PYTEST_FLAKY_MIN_RUNS: int = 3  # Minimum runs before detecting flaky tests
PYTEST_FLAKY_FAILURE_RATE: float = 0.3  # Consider flaky if fails >= 30% but < 100%


def extract_all_test_results_from_junit(junitxml_path: str) -> dict[str, str] | None:
    """Extract all test results from JUnit XML file.

    Args:
        junitxml_path: Path to JUnit XML file.

    Returns:
        dict[str, str] | None: Dictionary mapping node_id to status
            (PASSED/FAILED/ERROR), or None if file doesn't exist or can't be parsed.
    """
    xml_path = Path(junitxml_path)
    if not xml_path.exists():
        return None

    try:
        from defusedxml import ElementTree

        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        test_results: dict[str, str] = {}

        for testcase in root.findall(".//testcase"):
            file_path = testcase.get("file", "")
            class_name = testcase.get("classname", "")
            test_name = testcase.get("name", "")
            if file_path:
                if class_name:
                    node_id = f"{file_path}::{class_name}::{test_name}"
                else:
                    node_id = f"{file_path}::{test_name}"
            else:
                node_id = f"{class_name}::{test_name}" if class_name else test_name

            # Determine status
            if testcase.find("failure") is not None:
                status = "FAILED"
            elif testcase.find("error") is not None:
                status = "ERROR"
            elif testcase.find("skipped") is not None:
                status = "SKIPPED"
            else:
                status = "PASSED"

            test_results[node_id] = status

        return test_results
    except Exception as e:
        logger.debug(f"Failed to parse JUnit XML for all tests: {e}")
        return None


def get_cpu_count() -> int:
    """Get the number of available CPU cores.

    Returns:
        int: Number of CPU cores, minimum 1.
    """
    try:
        import multiprocessing

        return max(1, multiprocessing.cpu_count())
    except Exception:
        return 1


def get_parallel_workers_from_preset(
    preset: str,
    test_count: int | None = None,
) -> str:
    """Convert parallel preset to worker count.

    Args:
        preset: Preset name (auto, small, medium, large) or number as string.
        test_count: Optional test count for dynamic presets.

    Returns:
        str: Worker count string for pytest-xdist (-n flag).

    Raises:
        ValueError: If preset is invalid.
    """
    preset_lower = preset.lower()

    if preset_lower == "auto":
        return "auto"
    elif preset_lower == "small":
        return "2"
    elif preset_lower == "medium":
        return "4"
    elif preset_lower == "large":
        cpu_count = get_cpu_count()
        # Use up to 8 workers for large suites, but not more than CPU count
        return str(min(8, cpu_count))
    elif preset_lower.isdigit():
        # Already a number, return as-is
        return preset
    else:
        raise ValueError(
            f"Invalid parallel preset: {preset}. "
            "Must be one of: auto, small, medium, large, or a number",
        )


def is_ci_environment() -> bool:
    """Detect if running in a CI/CD environment.

    Checks for common CI environment variables:
    - CI (generic CI indicator)
    - GITHUB_ACTIONS (GitHub Actions)
    - GITLAB_CI (GitLab CI)
    - JENKINS_URL (Jenkins)
    - CIRCLE CI (CircleCI)
    - TRAVIS (Travis CI)
    - AZURE_HTTP_USER_AGENT (Azure DevOps)
    - TEAMCITY_VERSION (TeamCity)
    - BUILDKITE (Buildkite)
    - DRONE (Drone CI)

    Returns:
        bool: True if running in CI environment, False otherwise.
    """
    ci_indicators = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "CIRCLE_CI",
        "CIRCLECI",
        "TRAVIS",
        "AZURE_HTTP_USER_AGENT",
        "TEAMCITY_VERSION",
        "BUILDKITE",
        "DRONE",
    ]
    return any(os.environ.get(indicator) for indicator in ci_indicators)


def get_flaky_cache_path() -> Path:
    """Get the path to the flaky test cache file.

    Returns:
        Path: Path to the cache file.
    """
    cache_dir = Path(".pytest_cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "lintro_flaky_tests.json"


def load_flaky_test_history() -> dict[str, dict[str, int]]:
    """Load flaky test history from cache file.

    Returns:
        dict[str, dict[str, int]]: Dictionary mapping test node_id to status counts.
        Format: {node_id: {"passed": count, "failed": count, "error": count}}
    """
    cache_path = get_flaky_cache_path()
    if not cache_path.exists():
        return {}

    try:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug(f"Failed to load flaky test history: {e}")
        return {}


def save_flaky_test_history(history: dict[str, dict[str, int]]) -> None:
    """Save flaky test history to cache file.

    Args:
        history: Dictionary mapping test node_id to status counts.
    """
    cache_path = get_flaky_cache_path()
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        logger.debug(f"Failed to save flaky test history: {e}")


def update_flaky_test_history(
    issues: list[PytestIssue],
    all_test_results: dict[str, str] | None = None,
) -> dict[str, dict[str, int]]:
    """Update flaky test history with current test results.

    Args:
        issues: List of parsed test issues (failures/errors).
        all_test_results: Optional dictionary mapping node_id to status for all tests.
                         If None, only tracks failures from issues.

    Returns:
        dict[str, dict[str, int]]: Updated history dictionary.
    """
    history = load_flaky_test_history()

    # If we have full test results (e.g., from JUnit XML), use those
    if all_test_results:
        for node_id, status in all_test_results.items():
            if node_id not in history:
                history[node_id] = {"passed": 0, "failed": 0, "error": 0}

            if status == "FAILED":
                history[node_id]["failed"] += 1
            elif status == "ERROR":
                history[node_id]["error"] += 1
            elif status == "PASSED":
                history[node_id]["passed"] += 1
    else:
        # Only track failures from issues (simpler but less accurate)
        for issue in issues:
            # Skip Mock objects in tests - only process real PytestIssue objects
            if not isinstance(issue, PytestIssue):
                continue
            if issue.node_id and isinstance(issue.node_id, str):
                if issue.node_id not in history:
                    history[issue.node_id] = {"passed": 0, "failed": 0, "error": 0}

                if issue.test_status == "FAILED":
                    history[issue.node_id]["failed"] += 1
                elif issue.test_status == "ERROR":
                    history[issue.node_id]["error"] += 1

    save_flaky_test_history(history)
    return history


def detect_flaky_tests(
    history: dict[str, dict[str, int]],
    min_runs: int = PYTEST_FLAKY_MIN_RUNS,
    failure_rate: float = PYTEST_FLAKY_FAILURE_RATE,
) -> list[tuple[str, float]]:
    """Detect flaky tests from history.

    A test is considered flaky if:
    - It has been run at least min_runs times
    - It has failures but not 100% failure rate
    - Failure rate >= failure_rate threshold

    Args:
        history: Test history dictionary.
        min_runs: Minimum number of runs before considering flaky.
        failure_rate: Minimum failure rate to consider flaky (0.0 to 1.0).

    Returns:
        list[tuple[str, float]]: List of (test_node_id, failure_rate) tuples.
    """
    flaky_tests: list[tuple[str, float]] = []

    for node_id, counts in history.items():
        total_runs = (
            counts.get("passed", 0) + counts.get("failed", 0) + counts.get("error", 0)
        )

        if total_runs < min_runs:
            continue

        failed_count = counts.get("failed", 0) + counts.get("error", 0)
        current_failure_rate = failed_count / total_runs

        # Consider flaky if:
        # 1. Has failures (failure_rate > 0)
        # 2. Not always failing (failure_rate < 1.0)
        # 3. Failure rate >= threshold
        if 0 < current_failure_rate < 1.0 and current_failure_rate >= failure_rate:
            flaky_tests.append((node_id, current_failure_rate))

    # Sort by failure rate descending
    flaky_tests.sort(key=lambda x: x[1], reverse=True)
    return flaky_tests


def load_pytest_config() -> dict:
    """Load pytest configuration from pyproject.toml or pytest.ini.

    Priority order (highest to lowest):
    1. pyproject.toml [tool.pytest.ini_options] (pytest convention)
    2. pyproject.toml [tool.pytest] (backward compatibility)
    3. pytest.ini [pytest]

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
                    pytest_tool_data = pyproject_data["tool"]["pytest"]
                    # Check for ini_options first (pytest convention)
                    if (
                        isinstance(pytest_tool_data, dict)
                        and "ini_options" in pytest_tool_data
                    ):
                        config = pytest_tool_data["ini_options"]
                    # Fall back to direct pytest config (backward compatibility)
                    elif isinstance(pytest_tool_data, dict):
                        config = pytest_tool_data
        except Exception as e:
            logger.warning(
                f"Failed to load pytest configuration from pyproject.toml: {e}",
            )

    # Check pytest.ini (lowest priority, updates existing config)
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


def load_lintro_ignore() -> list[str]:
    """Load ignore patterns from .lintro-ignore file.

    Returns:
        list[str]: List of ignore patterns.
    """
    from lintro.utils.path_utils import find_lintro_ignore

    ignore_patterns: list[str] = []
    ignore_file = find_lintro_ignore()

    if ignore_file and ignore_file.exists():
        try:
            with open(ignore_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception as e:
            logger.warning(f"Failed to load .lintro-ignore: {e}")

    return ignore_patterns


def load_file_patterns_from_config(
    pytest_config: dict,
) -> list[str]:
    """Load file patterns from pytest configuration.

    Args:
        pytest_config: Pytest configuration dictionary.

    Returns:
        list[str]: File patterns from config, or empty list if not configured.
    """
    if not pytest_config:
        return []

    # Get python_files from config
    python_files = pytest_config.get("python_files")
    if not python_files:
        return []

    # Handle both string and list formats
    if isinstance(python_files, str):
        # Split on whitespace and commas
        patterns = [
            p.strip() for p in python_files.replace(",", " ").split() if p.strip()
        ]
        return patterns
    elif isinstance(python_files, list):
        return python_files
    else:
        logger.warning(f"Unexpected python_files type: {type(python_files)}")
        return []


def initialize_pytest_tool_config(tool) -> None:
    """Initialize pytest tool configuration from config files.

    Loads pytest config, file patterns, and default options.
    Updates tool.config.file_patterns and tool.options.

    Args:
        tool: PytestTool instance to initialize.
    """
    # Load pytest configuration
    pytest_config = load_pytest_config()

    # Load file patterns from config if available
    config_file_patterns = load_file_patterns_from_config(pytest_config)
    if config_file_patterns:
        # Override default patterns with config patterns
        tool.config.file_patterns = config_file_patterns

    # Set default options based on configuration
    default_options = {
        "verbose": True,
        "tb": "short",  # Traceback format
        "maxfail": None,  # Don't stop early - run all tests
        "no_header": True,
        "disable_warnings": True,
    }

    # Override with config file settings
    if pytest_config and "addopts" in pytest_config:
        # Parse addopts string with proper handling of quoted values
        tokens = shlex.split(pytest_config["addopts"])
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            idx += 1
            if not token.startswith("-"):
                continue

            key = token.lstrip("-")
            value: object = True
            if "=" in key:
                key, raw = key.split("=", 1)
                value = raw
            elif idx < len(tokens) and not tokens[idx].startswith("-"):
                value = tokens[idx]
                idx += 1

            option_key = key.replace("-", "_")
            default_options[option_key] = value

    tool.options.update(default_options)


def check_plugin_installed(plugin_name: str) -> bool:
    """Check if a pytest plugin is installed.

    Args:
        plugin_name: Name of the plugin to check (e.g., 'pytest-cov').

    Returns:
        bool: True if plugin is installed, False otherwise.
    """
    import importlib.metadata

    # Try to find the plugin package
    try:
        importlib.metadata.distribution(plugin_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        # Try alternative names (e.g., pytest-cov -> pytest_cov)
        alt_name = plugin_name.replace("-", "_")
        try:
            importlib.metadata.distribution(alt_name)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False


def list_installed_plugins() -> list[dict[str, str]]:
    """List all installed pytest plugins.

    Returns:
        list[dict[str, str]]: List of plugin information dictionaries with
            'name' and 'version' keys.
    """
    plugins: list[dict[str, str]] = []

    import importlib.metadata

    # Get all installed packages
    distributions = importlib.metadata.distributions()

    # Filter for pytest plugins
    for dist in distributions:
        dist_name = dist.metadata.get("Name", "")
        if dist_name.startswith("pytest-") or dist_name.startswith("pytest_"):
            version = dist.metadata.get("Version", "unknown")
            plugins.append({"name": dist_name, "version": version})

    # Sort by name
    plugins.sort(key=lambda x: x["name"])
    return plugins


def get_pytest_version_info() -> str:
    """Get pytest version and plugin information.

    Returns:
        str: Formatted string with pytest version and plugin list.
    """
    try:
        cmd = ["pytest", "--version"]
        result = subprocess.run(  # nosec B603 - pytest is a trusted executable
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return "pytest version information unavailable"


def collect_tests_once(
    tool,
    target_files: list[str],
) -> tuple[int, int]:
    """Collect tests once and return both total count and docker test count.

    This function optimizes test collection by running pytest --collect-only
    once and extracting both metrics from the same output, avoiding the
    overhead of duplicate collection calls.

    Args:
        tool: PytestTool instance.
        target_files: Files or directories to check.

    Returns:
        tuple[int, int]: Tuple of (total_test_count, docker_test_count).
    """
    import re

    try:
        # Use pytest --collect-only to list all tests
        collect_cmd = tool._get_executable_command(tool_name="pytest")
        collect_cmd.append("--collect-only")
        collect_cmd.extend(target_files)

        # Temporarily enable all tests to see total count
        original_docker_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")
        os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"

        try:
            success, output = tool._run_subprocess(collect_cmd)
            if not success:
                return (0, 0)

            # Extract the total count from collection output
            # Format: "XXXX tests collected in Y.YYs"
            total_count = 0
            match = re.search(r"(\d+)\s+tests\s+collected", output)
            if match:
                total_count = int(match.group(1))

            # Count docker tests from the same output
            # Track when we're inside the docker directory and count Function items
            docker_test_count = 0
            in_docker_dir = False
            depth = 0

            for line in output.splitlines():
                # Stop counting when we hit coverage section
                if "coverage:" in line or "TOTAL" in line:
                    break

                stripped = line.strip()

                # Check if we're entering the docker directory
                if "<Dir docker>" in line or "<Package docker>" in line:
                    in_docker_dir = True
                    depth = len(line) - len(stripped)  # Track indentation level
                    continue

                # Check if we're leaving the docker directory
                # (next directory at same or higher level)
                if in_docker_dir and stripped.startswith("<"):
                    current_depth = len(line) - len(stripped)
                    if current_depth <= depth and not stripped.startswith(
                        "<Function",
                    ):
                        # We've left the docker directory
                        # (backed up to same or higher level)
                        in_docker_dir = False
                        continue

                # Count Function items while inside docker directory
                if in_docker_dir and "<Function" in line:
                    docker_test_count += 1

            return (total_count, docker_test_count)
        finally:
            # Restore original environment
            if original_docker_env is not None:
                os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_docker_env
            elif "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]
    except Exception as e:
        logger.debug(f"Failed to collect tests: {e}")
        return (0, 0)


def get_total_test_count(
    tool,
    target_files: list[str],
) -> int:
    """Get total count of all available tests (including deselected ones).

    Note: This function is kept for backward compatibility but delegates to
    collect_tests_once() for efficiency. Consider using collect_tests_once()
    directly if you also need docker test count.

    Args:
        tool: PytestTool instance.
        target_files: Files or directories to check.

    Returns:
        int: Total number of tests that exist.
    """
    total_count, _ = collect_tests_once(tool, target_files)
    return total_count


def count_docker_tests(
    tool,
    target_files: list[str],
) -> int:
    """Count docker tests that would be skipped.

    Note: This function is kept for backward compatibility but delegates to
    collect_tests_once() for efficiency. Consider using collect_tests_once()
    directly if you also need total test count.

    Args:
        tool: PytestTool instance.
        target_files: Files or directories to check.

    Returns:
        int: Number of docker tests found.
    """
    _, docker_count = collect_tests_once(tool, target_files)
    return docker_count
