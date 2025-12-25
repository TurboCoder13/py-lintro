"""Tests for pyproject config hydration in ``BanditTool.__post_init__``."""

import io
import os
from contextlib import contextmanager

from assertpy import assert_that

from lintro.tools.implementations.tool_bandit import BanditTool


@contextmanager
def temp_pyproject(content: str):
    """Temporarily write a pyproject.toml with provided content.

    Args:
        content: TOML to write while the context manager is active.

    Yields:
        None: Context in which the temporary file is present.
    """
    path = "pyproject.toml"
    exists = os.path.exists(path)
    backup = None
    try:
        if exists:
            with open(path, "rb") as f:
                backup = f.read()
        with open(path, "wb") as f:
            f.write(content.encode())
        yield
    finally:
        if backup is not None:
            with open(path, "wb") as f:
                f.write(backup)
        elif os.path.exists(path):
            os.remove(path)


def test_hydrates_severity_confidence_from_pyproject() -> None:
    """Hydrate severity/confidence values from pyproject settings."""
    io.BytesIO()
    toml_content = '[tool.bandit]\nseverity = "HIGH"\nconfidence = "MEDIUM"\n'
    with temp_pyproject(toml_content):
        tool = BanditTool()
        assert_that(tool.options.get("severity")).is_equal_to("HIGH")
        assert_that(tool.options.get("confidence")).is_equal_to("MEDIUM")
