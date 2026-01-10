"""Tests for CommandChainer.group_commands method."""

from __future__ import annotations

import click
from assertpy import assert_that

from lintro.cli_utils.command_chainer import CommandChainer


def test_group_single_command(mock_group: click.Group) -> None:
    """Test grouping of a single command.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.group_commands(["fmt", "."])

    assert_that(result).is_equal_to([["fmt", "."]])


def test_group_two_commands(mock_group: click.Group) -> None:
    """Test grouping of two commands.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.group_commands(["fmt", ".", ",", "chk", "."])

    assert_that(result).is_equal_to([["fmt", "."], ["chk", "."]])


def test_group_three_commands(mock_group: click.Group) -> None:
    """Test grouping of three commands.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.group_commands(["fmt", ",", "chk", ",", "tst"])

    assert_that(result).is_equal_to([["fmt"], ["chk"], ["tst"]])


def test_group_empty_args(mock_group: click.Group) -> None:
    """Test grouping of empty args.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.group_commands([])

    assert_that(result).is_equal_to([])


def test_group_ignores_empty_groups(mock_group: click.Group) -> None:
    """Test that empty groups from consecutive separators are ignored.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    result = chainer.group_commands(["fmt", ",", ",", "chk"])

    assert_that(result).is_equal_to([["fmt"], ["chk"]])
