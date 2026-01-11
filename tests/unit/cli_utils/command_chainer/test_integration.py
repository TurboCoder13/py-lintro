"""Integration tests for CommandChainer full workflow."""

from __future__ import annotations

import click
from assertpy import assert_that

from lintro.cli_utils.command_chainer import CommandChainer


def test_full_workflow_parse_and_group(mock_group: click.Group) -> None:
    """Test complete workflow from raw args to command groups.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    raw_args = ["fmt", ".", ",", "chk", ".", ",", "tst"]

    assert_that(chainer.should_chain(raw_args)).is_true()

    normalized = chainer.normalize_args(raw_args)
    assert_that(normalized).is_equal_to(raw_args)

    groups = chainer.group_commands(normalized)
    assert_that(groups).is_equal_to([["fmt", "."], ["chk", "."], ["tst"]])


def test_full_workflow_joined_commands(mock_group: click.Group) -> None:
    """Test workflow with joined commands like fmt,chk.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    raw_args = ["fmt,chk", "."]

    assert_that(chainer.should_chain(raw_args)).is_true()

    normalized = chainer.normalize_args(raw_args)
    assert_that(normalized).is_equal_to(["fmt", ",", "chk", "."])

    groups = chainer.group_commands(normalized)
    assert_that(groups).is_equal_to([["fmt"], ["chk", "."]])
