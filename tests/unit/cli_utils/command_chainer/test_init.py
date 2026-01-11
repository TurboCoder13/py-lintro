"""Tests for CommandChainer initialization and command_names property."""

from __future__ import annotations

import click
from assertpy import assert_that

from lintro.cli_utils.command_chainer import CommandChainer


def test_init_with_default_separator(mock_group: click.Group) -> None:
    """Test initialization with default comma separator.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    assert_that(chainer.group).is_equal_to(mock_group)
    assert_that(chainer.separator).is_equal_to(",")
    assert_that(chainer._command_names).is_none()


def test_init_with_custom_separator(mock_group: click.Group) -> None:
    """Test initialization with custom separator.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group, separator=";")

    assert_that(chainer.separator).is_equal_to(";")


def test_command_names_lazy_loading(mock_group: click.Group) -> None:
    """Test that command names are loaded lazily.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    assert_that(chainer._command_names).is_none()

    names = chainer.command_names

    assert_that(names).contains("fmt", "chk", "tst")
    assert_that(chainer._command_names).is_not_none()


def test_command_names_cached(mock_group: click.Group) -> None:
    """Test that command names are cached after first access.

    Args:
        mock_group: Mocked Click group fixture.
    """
    chainer = CommandChainer(mock_group)

    names1 = chainer.command_names
    names2 = chainer.command_names

    assert_that(names1).is_same_as(names2)
