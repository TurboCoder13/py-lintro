"""Tests for CommandChainer.normalize_args method."""

from __future__ import annotations

import click
from assertpy import assert_that

from lintro.cli_utils.command_chainer import CommandChainer


def test_normalize_already_separated(mock_group: click.Group) -> None:
    """Test normalization of already separated args.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.normalize_args(["fmt", ",", "chk"])

    assert_that(result).is_equal_to(["fmt", ",", "chk"])


def test_normalize_joined_commands(mock_group: click.Group) -> None:
    """Test normalization of joined command names.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.normalize_args(["fmt,chk"])

    assert_that(result).is_equal_to(["fmt", ",", "chk"])


def test_normalize_preserves_arguments(mock_group: click.Group) -> None:
    """Test that command arguments are preserved.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.normalize_args(["fmt", ".", ",", "chk", "."])

    assert_that(result).is_equal_to(["fmt", ".", ",", "chk", "."])


def test_normalize_preserves_comma_in_option_value(mock_group: click.Group) -> None:
    """Test that comma in option values is preserved.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.normalize_args(["fmt", "--tools", "ruff,bandit"])

    assert_that(result).is_equal_to(["fmt", "--tools", "ruff,bandit"])


def test_normalize_multiple_commands(mock_group: click.Group) -> None:
    """Test normalization of multiple chained commands.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.normalize_args(["fmt,chk,tst"])

    assert_that(result).is_equal_to(["fmt", ",", "chk", ",", "tst"])
