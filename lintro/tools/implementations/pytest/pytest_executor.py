"""Pytest execution logic.

This module contains the PytestExecutor class that handles test execution,
environment management, and subprocess operations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from lintro.tools.implementations.pytest.collection import get_cpu_count
from lintro.tools.implementations.pytest.markers import collect_tests_once
from lintro.tools.implementations.pytest.pytest_config import PytestConfiguration

if TYPE_CHECKING:
    from lintro.tools.definitions.pytest import PytestPlugin


@dataclass
class PytestExecutor:
    """Handles pytest test execution and environment management.

    This class encapsulates the logic for executing pytest tests, managing
    Docker test environment variables, and handling subprocess operations.

    Attributes:
        config: PytestConfiguration instance with test execution options.
        tool: Reference to the parent tool for subprocess execution.
    """

    config: PytestConfiguration
    tool: PytestPlugin | None  # Required: must be set by the parent tool

    def prepare_test_execution(
        self,
        target_files: list[str],
    ) -> tuple[int, int, str | None]:
        """Prepare test execution by collecting tests and setting up environment.

        Args:
            target_files: Files or directories to test.

        Raises:
            ValueError: If tool reference is not set.

        Returns:
            Tuple[int, int, str | None]: Tuple of (total_available_tests,
                docker_test_count, original_docker_env).
        """
        if self.tool is None:
            raise ValueError("Tool reference not set on executor")

        # Docker tests are disabled by default and must be explicitly enabled
        run_docker_tests = self.config.run_docker_tests or False

        # Store original environment state for cleanup
        original_docker_env = os.environ.get("LINTRO_RUN_DOCKER_TESTS")

        # Collect tests once and get both total count and docker test count
        # This avoids duplicate pytest --collect-only calls
        total_available_tests, docker_test_count = collect_tests_once(
            self.tool,
            target_files,
        )

        if run_docker_tests:
            # Set environment variable to enable Docker tests
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = "1"
            # Log that Docker tests are enabled (may take longer) in blue format
            docker_msg = (
                f"[LINTRO] Docker tests enabled ({docker_test_count} tests) - "
                "this may take longer than usual."
            )
            logger.info(f"\033[36;1m{docker_msg}\033[0m")
        else:
            # Explicitly unset the environment variable to disable Docker tests
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]

            if docker_test_count > 0:
                # Log that Docker tests are disabled in blue format
                docker_msg = (
                    f"[LINTRO] Docker tests disabled "
                    f"({docker_test_count} tests not collected). "
                    "Use --enable-docker to include them."
                )
                logger.info(f"\033[36;1m{docker_msg}\033[0m")

        return (total_available_tests, docker_test_count, original_docker_env)

    def execute_tests(
        self,
        cmd: list[str],
    ) -> tuple[bool, str, int]:
        """Execute pytest tests and parse output.

        Args:
            cmd: Command to execute.

        Raises:
            ValueError: If tool reference is not set.

        Returns:
            Tuple[bool, str, int]: Tuple of (success, output, return_code).
        """
        if self.tool is None:
            raise ValueError("Tool reference not set on executor")

        success, output = self.tool._run_subprocess(cmd)
        # Parse output with actual success status
        # (pytest returns non-zero on failures)
        return_code = 0 if success else 1
        return (success, output, return_code)

    def restore_environment(self, original_docker_env: str | None) -> None:
        """Restore the original environment state.

        Args:
            original_docker_env: Original value of LINTRO_RUN_DOCKER_TESTS env var.
        """
        # Restore original environment state
        if original_docker_env is not None:
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_docker_env
        elif "LINTRO_RUN_DOCKER_TESTS" in os.environ:
            del os.environ["LINTRO_RUN_DOCKER_TESTS"]

    def display_run_config(
        self,
        total_tests: int,
        target_files: list[str],
    ) -> None:
        """Display test run configuration summary.

        Args:
            total_tests: Total number of tests discovered.
            target_files: List of target files/directories.
        """
        import click

        options = self.config.get_options_dict()

        # Get worker configuration
        workers = options.get("workers")
        parallel_preset = options.get("parallel_preset")
        if parallel_preset:
            worker_display = f"{parallel_preset} preset"
        elif workers == "auto" or workers is None:
            cpu_count = get_cpu_count()
            worker_display = f"auto ({cpu_count} CPUs)"
        elif workers and str(workers) != "0":
            worker_display = str(workers)
        else:
            worker_display = "disabled"

        # Get coverage configuration
        coverage_enabled = any(
            [
                options.get("coverage_term_missing"),
                options.get("coverage_html"),
                options.get("coverage_xml"),
                options.get("coverage_report"),
            ],
        )
        coverage_display = "enabled" if coverage_enabled else "disabled"

        # Format paths display
        if len(target_files) == 1:
            paths_display = target_files[0]
        elif len(target_files) <= 3:
            paths_display = ", ".join(target_files)
        else:
            paths_display = f"{target_files[0]} (+{len(target_files) - 1} more)"

        # Build and display config summary
        config_line = (
            f"Tests: {total_tests} | "
            f"Parallel: {worker_display} | "
            f"Coverage: {coverage_display} | "
            f"Path: {paths_display}"
        )
        click.echo(click.style(f"[LINTRO] {config_line}", fg="cyan"))
