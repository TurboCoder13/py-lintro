"""Tests for BlackPlugin line length checking."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_check_line_length_violations_empty_files(black_plugin: BlackPlugin) -> None:
    """Returns empty list when no files provided.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    result = black_plugin._check_line_length_violations(files=[], cwd="/tmp")
    assert_that(result).is_empty()


def test_check_line_length_violations_with_violations(
    black_plugin: BlackPlugin,
) -> None:
    """Returns violations when lines exceed limit.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    from lintro.tools.core.line_length_checker import LineLengthViolation

    with patch(
        "lintro.tools.core.line_length_checker.check_line_length_violations",
    ) as mock_check:
        mock_check.return_value = [
            LineLengthViolation(
                file="test.py",
                line=10,
                column=89,
                code="E501",
                message="89 > 88 characters",
            ),
        ]

        black_plugin.set_options(line_length=88)
        result = black_plugin._check_line_length_violations(
            files=["test.py"],
            cwd="/tmp",
        )

        assert_that(result).is_length(1)
        assert_that(result[0].file).is_equal_to("test.py")
        assert_that(result[0].line).is_equal_to(10)
        assert_that(result[0].fixable).is_false()
