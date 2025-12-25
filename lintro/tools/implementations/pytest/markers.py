"""Pytest marker and plugin utility functions."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess used safely with shell=False

from loguru import logger


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
