"""Centralized logging utility for Lintro using loguru."""

from loguru import logger
import datetime
import pathlib
import threading

_LOGGER_CONFIGURED = False
_LOGGER_LOCK = threading.Lock()


def format_timestamp() -> str:
    """Format current time as @/HH:MM:SS.

    Returns:
        Formatted timestamp string.
    """
    now = datetime.datetime.now()
    return f"@/{now.strftime('%H:%M:%S')}"


def _can_write_to_directory(path: pathlib.Path) -> bool:
    """Check if we can write to the given directory.

    Args:
        path: Directory path to check

    Returns:
        True if writable, False otherwise
    """
    try:
        # Try to create a test file
        test_file = path / ".test_write"
        test_file.touch()
        test_file.unlink()
        return True
    except (OSError, PermissionError):
        return False


def get_logger(verbose: bool = False) -> logger.__class__:
    """Get the global loguru logger, configured for Lintro's log directory structure.

    Args:
        verbose: Whether to enable verbose logging (DEBUG level for console)

    Returns:
        logger.__class__: Configured loguru logger instance.

    Raises:
        PermissionError: If unable to create or write to log directory
    """
    global _LOGGER_CONFIGURED
    with _LOGGER_LOCK:
        if not _LOGGER_CONFIGURED:
            now = datetime.datetime.now()

            # Try to create log directory, fall back to console-only if it fails
            log_dir = pathlib.Path(
                f"logs/{now.year}/{now.strftime('%m-%b')}/{now.strftime('%d.%m.%Y')}/{now.strftime('%H:%M:%S')}/files"
            )

            # Remove default handler
            logger.remove()

            # Try to set up file logging
            try:
                log_dir.mkdir(parents=True, exist_ok=True)

                # Check if we can actually write to the directory
                if _can_write_to_directory(log_dir):
                    log_file = log_dir / "lintro.log"

                    # Add file handler with detailed format
                    logger.add(
                        str(log_file),
                        rotation="10 MB",
                        retention="10 days",
                        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                    )
                else:
                    # Directory exists but we can't write to it
                    raise PermissionError("Cannot write to log directory")

            except (OSError, PermissionError) as e:
                # Fall back to console-only logging
                logger.warning(
                    f"File logging disabled: {e}. Using console-only logging."
                )

            # Add console handler with timestamp format
            console_level = "DEBUG" if verbose else "WARNING"
            logger.add(
                lambda msg: print(f"{format_timestamp()} {msg}"),
                format="{message}",
                level=console_level,
            )

            logger.info("Lintro started at {}", now.isoformat())
            _LOGGER_CONFIGURED = True
    return logger
