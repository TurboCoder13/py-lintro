"""Tests for pydoclint plugin _build_command method."""

from __future__ import annotations

from assertpy import assert_that

from lintro.tools.definitions.pydoclint import PydoclintPlugin


def test_build_command_basic(pydoclint_plugin: PydoclintPlugin) -> None:
    """Build basic command with default options.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    cmd = pydoclint_plugin._build_command()
    assert_that(cmd).contains("pydoclint")
    assert_that(cmd).contains("--style")
    assert_that(cmd).contains("google")


def test_build_command_with_style(pydoclint_plugin: PydoclintPlugin) -> None:
    """Build command with style option.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(style="numpy")
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).contains("--style")
    style_idx = cmd.index("--style")
    assert_that(cmd[style_idx + 1]).is_equal_to("numpy")


def test_build_command_with_check_return_types_false(
    pydoclint_plugin: PydoclintPlugin,
) -> None:
    """Build command with check_return_types disabled.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(check_return_types=False)
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).contains("--check-return-types")
    idx = cmd.index("--check-return-types")
    assert_that(cmd[idx + 1]).is_equal_to("false")


def test_build_command_with_check_arg_order_false(
    pydoclint_plugin: PydoclintPlugin,
) -> None:
    """Build command with check_arg_order disabled.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(check_arg_order=False)
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).contains("--check-arg-order")
    idx = cmd.index("--check-arg-order")
    assert_that(cmd[idx + 1]).is_equal_to("false")


def test_build_command_with_skip_short_docstrings_false(
    pydoclint_plugin: PydoclintPlugin,
) -> None:
    """Build command with skip_checking_short_docstrings disabled.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(skip_checking_short_docstrings=False)
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).contains("--skip-checking-short-docstrings")
    idx = cmd.index("--skip-checking-short-docstrings")
    assert_that(cmd[idx + 1]).is_equal_to("false")


def test_build_command_with_quiet_false(pydoclint_plugin: PydoclintPlugin) -> None:
    """Build command with quiet disabled.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(quiet=False)
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).does_not_contain("--quiet")


def test_build_command_with_all_options(pydoclint_plugin: PydoclintPlugin) -> None:
    """Build command with all options set.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
    """
    pydoclint_plugin.set_options(
        style="sphinx",
        check_return_types=True,
        check_arg_order=True,
        skip_checking_short_docstrings=True,
        quiet=True,
    )
    cmd = pydoclint_plugin._build_command()

    assert_that(cmd).contains("--style")
    assert_that(cmd).contains("--check-return-types")
    assert_that(cmd).contains("--check-arg-order")
    assert_that(cmd).contains("--skip-checking-short-docstrings")
    assert_that(cmd).contains("--quiet")

    # Verify boolean values are passed correctly (lowercase)
    crt_idx = cmd.index("--check-return-types")
    assert_that(cmd[crt_idx + 1]).is_equal_to("true")
    cao_idx = cmd.index("--check-arg-order")
    assert_that(cmd[cao_idx + 1]).is_equal_to("true")
    scsd_idx = cmd.index("--skip-checking-short-docstrings")
    assert_that(cmd[scsd_idx + 1]).is_equal_to("true")
