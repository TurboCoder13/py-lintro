"""Environment utilities for subprocess execution."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from loguru import logger


def get_subprocess_env() -> dict[str, str]:
    """Build an environment dict suitable for subprocess calls.

    Copies the current environment and ensures HOME points to a writable
    directory.  When the real HOME is missing, not a directory, or not
    writable (e.g., Docker with ``--user "$(id -u):$(id -g)"``), HOME is
    redirected to the system temp directory so tools that need cache or
    config directories under ``$HOME`` don't fail with permission errors.

    Returns:
        A copy of ``os.environ`` with HOME guaranteed to be writable.
    """
    env = os.environ.copy()
    home = env.get("HOME", "")
    if not home or not Path(home).is_dir() or not os.access(home, os.W_OK):
        env["HOME"] = tempfile.gettempdir()
        logger.debug(
            "[env] HOME '{}' is unwritable, redirecting to {}",
            home,
            env["HOME"],
        )
    return env
