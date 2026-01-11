"""Pytest marker and plugin utility functions."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from lintro.tools.definitions.pytest import PytestPlugin


def check_plugin_installed(plugin_name: str) -> bool:
    """Check if a pytest plugin is installed.

    Checks for the plugin using importlib.metadata, trying both the exact name
    and an alternative name with hyphens replaced by underscores (e.g., "pytest-cov"
    and "pytest_cov").

    Args:
        plugin_name: Name of the plugin to check (e.g., 'pytest-cov', 'pytest-xdist').

    Returns:
        bool: True if plugin is installed (found under either name), False otherwise.

    Examples:
        >>> check_plugin_installed("pytest-cov")
        True  # if pytest-cov is installed
        >>> check_plugin_installed("pytest-nonexistent")
        False
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

    Scans all installed Python packages and filters for those whose names start
    with "pytest-" or "pytest_". Returns plugin information including name and version.

    Returns:
        list[dict[str, str]]: List of plugin information dictionaries, each containing:
            - 'name': Plugin package name (e.g., "pytest-cov")
            - 'version': Plugin version string (e.g., "4.1.0")
        List is sorted alphabetically by plugin name.

    Examples:
        >>> plugins = list_installed_plugins()
        >>> [p['name'] for p in plugins if 'cov' in p['name']]
        ['pytest-cov']
    """
    plugins: list[dict[str, str]] = []

    import importlib.metadata

    # Get all installed packages
    distributions = importlib.metadata.distributions()

    # Filter for pytest plugins
    for dist in distributions:
        dist_name = dist.metadata["Name"] or ""
        if dist_name.startswith("pytest-") or dist_name.startswith("pytest_"):
            version = dist.metadata["Version"] or "unknown"
            plugins.append({"name": dist_name, "version": version})

    # Sort by name
    plugins.sort(key=lambda x: x["name"])
    return plugins


def get_pytest_version_info() -> str:
    """Get pytest version and plugin information.

    Executes `pytest --version` to retrieve version information. Handles errors
    gracefully by returning a fallback message if the command fails.

    Returns:
        str: Formatted string with pytest version information from stdout.
            Returns "pytest version information unavailable" if the command
            fails or times out.

    Examples:
        >>> version_info = get_pytest_version_info()
        >>> "pytest" in version_info.lower()
        True
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
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug(f"Failed to get pytest version: {e}")
        return "pytest version information unavailable"


def collect_tests_once(
    tool: PytestPlugin,
    target_files: list[str],
) -> tuple[int, int]:
    """Collect tests once and return both total count and docker test count.

    This function optimizes test collection by running pytest --collect-only
    once and extracting both metrics from the same output, avoiding the
    overhead of duplicate collection calls. It parses the collection output
    to count total tests and specifically identifies docker tests by tracking
    directory structure in the output.

    Args:
        tool: PytestTool instance with _get_executable_command and _run_subprocess
            methods. Must support running pytest commands.
        target_files: List of file paths or directory paths to check for tests.
            These are passed directly to pytest --collect-only.

    Returns:
        tuple[int, int]: Tuple containing:
            - total_test_count: Total number of tests found (including docker tests)
            - docker_test_count: Number of tests in docker directories
        Returns (0, 0) if collection fails or no tests are found.

    Examples:
        >>> tool = PytestTool(...)
        >>> total, docker = collect_tests_once(tool, ["tests/"])
        >>> total >= docker
        True
    """
    import re

    try:
        # Use pytest --collect-only to list all tests
        collect_cmd = tool._get_executable_command(tool_name="pytest")
        collect_cmd.append("--collect-only")
        collect_cmd.extend(target_files)

        # Enable all tests to see total count via subprocess environment
        env = os.environ.copy()
        env["LINTRO_RUN_DOCKER_TESTS"] = "1"

        success, output = tool._run_subprocess(collect_cmd, env=env)
        if not success:
            return (0, 0)

        # Extract the total count from collection output
        # Format: "XXXX tests collected in Y.YYs" or "1 test collected"
        total_count = 0
        match = re.search(r"(\d+)\s+tests?\s+collected", output)
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
    except (OSError, ValueError, RuntimeError) as e:
        logger.debug(f"Failed to collect tests: {e}")
        return (0, 0)


def get_total_test_count(
    tool: PytestPlugin,
    target_files: list[str],
) -> int:
    """Get total count of all available tests (including deselected ones).

    This function is kept for backward compatibility but delegates to
    collect_tests_once() for efficiency. Consider using collect_tests_once()
    directly if you also need docker test count.

    Args:
        tool: PytestTool instance with _get_executable_command and _run_subprocess
            methods. Must support running pytest commands.
        target_files: List of file paths or directory paths to check for tests.
            These are passed directly to pytest --collect-only.

    Returns:
        int: Total number of tests that exist (including docker tests).
            Returns 0 if collection fails or no tests are found.

    Examples:
        >>> tool = PytestTool(...)
        >>> count = get_total_test_count(tool, ["tests/"])
        >>> count >= 0
        True
    """
    total_count, _ = collect_tests_once(tool, target_files)
    return total_count


def count_docker_tests(
    tool: PytestPlugin,
    target_files: list[str],
) -> int:
    """Count docker tests that would be skipped.

    This function is kept for backward compatibility but delegates to
    collect_tests_once() for efficiency. Consider using collect_tests_once()
    directly if you also need total test count.

    Args:
        tool: PytestTool instance with _get_executable_command and _run_subprocess
            methods. Must support running pytest commands.
        target_files: List of file paths or directory paths to check for tests.
            These are passed directly to pytest --collect-only.

    Returns:
        int: Number of docker tests found in docker directories.
            Returns 0 if collection fails or no docker tests are found.

    Examples:
        >>> tool = PytestTool(...)
        >>> docker_count = count_docker_tests(tool, ["tests/"])
        >>> docker_count >= 0
        True
    """
    _, docker_count = collect_tests_once(tool, target_files)
    return docker_count
