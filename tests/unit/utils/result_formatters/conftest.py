"""Shared fixtures for result_formatters tests.

Note: console_capture_with_kwargs is inherited from tests/unit/utils/conftest.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def success_capture() -> tuple[Callable[[str], None], list[str]]:
    """Capture success function calls.

    Returns a tuple containing:
    - capture function that appends messages
    - output list containing captured messages

    Returns:
        A tuple of (capture_function, output_list).
    """
    calls: list[str] = []

    def capture(message: str = "") -> None:
        calls.append(message)

    return capture, calls
