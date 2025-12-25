"""Output processing functions for pytest tool.

This module contains output parsing, summary extraction, performance warnings,
and flaky test detection logic extracted from PytestTool to improve
maintainability and reduce file size.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from loguru import logger

# Constants for pytest configuration
PYTEST_FLAKY_MIN_RUNS: int = 3
PYTEST_FLAKY_FAILURE_RATE: float = 0.3
PYTEST_SLOW_TEST_THRESHOLD: float = 1.0
PYTEST_TOTAL_TIME_WARNING: float = 60.0

# Path to flaky test history file
FLAKY_TEST_HISTORY_PATH = Path(".lintro/flaky_test_history.json")


def load_flaky_test_history() -> dict[str, dict[str, int]]:
    """Load flaky test history from disk.

    Returns:
        dict[str, dict[str, int]]: Test history dictionary.
    """
    if not FLAKY_TEST_HISTORY_PATH.exists():
        return {}

    try:
        with open(FLAKY_TEST_HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"Failed to load flaky test history: {e}")
        return {}


def save_flaky_test_history(history: dict[str, dict[str, int]]) -> None:
    """Save flaky test history to disk.

    Args:
        history: Test history dictionary to save.
    """
    try:
        FLAKY_TEST_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAKY_TEST_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        logger.debug(f"Failed to save flaky test history: {e}")


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


# Module-level cache for pytest config to avoid repeated file parsing
_PYTEST_CONFIG_CACHE: dict[tuple[str, float, float], dict] = {}


def clear_pytest_config_cache() -> None:
    """Clear the pytest config cache.

    This function is primarily intended for testing to ensure
    config files are re-read when needed.
    """
    _PYTEST_CONFIG_CACHE.clear()


def load_pytest_config() -> dict:
    """Load pytest configuration from pyproject.toml or pytest.ini.

    Priority order (highest to lowest):
    1. pyproject.toml [tool.pytest.ini_options] (pytest convention)
    2. pyproject.toml [tool.pytest] (backward compatibility)
    3. pytest.ini [pytest]

    This function uses caching to avoid repeatedly parsing config files
    during the same process run. Cache is keyed by working directory and
    file modification times to ensure freshness.

    Returns:
        dict: Pytest configuration dictionary.
    """
    cwd = os.getcwd()
    pyproject_path = Path("pyproject.toml")
    pytest_ini_path = Path("pytest.ini")

    # Create cache key from working directory and file modification times
    cache_key = (
        cwd,
        pyproject_path.stat().st_mtime if pyproject_path.exists() else 0.0,
        pytest_ini_path.stat().st_mtime if pytest_ini_path.exists() else 0.0,
    )

    # Return cached result if available
    if cache_key in _PYTEST_CONFIG_CACHE:
        return _PYTEST_CONFIG_CACHE[cache_key].copy()

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

    # Cache the result
    _PYTEST_CONFIG_CACHE[cache_key] = config.copy()
    return config


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

    # Override with config file settings
