"""Loguru logger configuration for Lintro.

Handles setup of logging handlers and configuration.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_loguru(run_dir: Path) -> None:
    """Configure Loguru with clean, simple handlers.

    Args:
        run_dir: Directory for log files.
    """
    # Remove default handler
    logger.remove()

    # Add console handler (for immediate display)
    # Only capture WARNING and ERROR for console
    logger.add(
        sys.stderr,
        level="WARNING",  # Only show warnings and errors
        format="{message}",  # Simple format without timestamps/log levels
        colorize=True,
    )

    # Add debug.log handler (captures everything)
    run_dir.mkdir(parents=True, exist_ok=True)
    debug_log_path: Path = run_dir / "debug.log"
    logger.add(
        debug_log_path,
        level="DEBUG",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        rotation=None,  # Append to same debug.log file across runs
    )
