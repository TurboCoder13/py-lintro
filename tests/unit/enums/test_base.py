"""Tests for base StrEnum utility classes."""

from __future__ import annotations

from enum import auto

from assertpy import assert_that

from lintro.enums.base import HyphenatedStrEnum, UpperCaseStrEnum


def test_upper_case_str_enum_single_word() -> None:
    """UpperCaseStrEnum produces uppercase values for single-word members."""

    class TestEnum(UpperCaseStrEnum):
        HEAD = auto()
        MAIN = auto()
        MASTER = auto()

    assert_that(TestEnum.HEAD.value).is_equal_to("HEAD")
    assert_that(TestEnum.MAIN.value).is_equal_to("MAIN")
    assert_that(TestEnum.MASTER.value).is_equal_to("MASTER")


def test_upper_case_str_enum_with_underscores() -> None:
    """UpperCaseStrEnum produces uppercase values preserving underscores."""

    class TestEnum(UpperCaseStrEnum):
        REV_PARSE = auto()
        GIT_COMMAND = auto()

    assert_that(TestEnum.REV_PARSE.value).is_equal_to("REV_PARSE")
    assert_that(TestEnum.GIT_COMMAND.value).is_equal_to("GIT_COMMAND")


def test_hyphenated_str_enum_single_word() -> None:
    """HyphenatedStrEnum produces lowercase values for single-word members."""

    class TestEnum(HyphenatedStrEnum):
        DESCRIBE = auto()
        LOG = auto()
        STATUS = auto()

    assert_that(TestEnum.DESCRIBE.value).is_equal_to("describe")
    assert_that(TestEnum.LOG.value).is_equal_to("log")
    assert_that(TestEnum.STATUS.value).is_equal_to("status")


def test_hyphenated_str_enum_with_underscores() -> None:
    """HyphenatedStrEnum converts underscores to hyphens."""

    class TestEnum(HyphenatedStrEnum):
        REV_PARSE = auto()
        GIT_COMMAND = auto()
        MULTI_WORD_NAME = auto()

    assert_that(TestEnum.REV_PARSE.value).is_equal_to("rev-parse")
    assert_that(TestEnum.GIT_COMMAND.value).is_equal_to("git-command")
    assert_that(TestEnum.MULTI_WORD_NAME.value).is_equal_to("multi-word-name")


def test_hyphenated_str_enum_multiple_underscores() -> None:
    """HyphenatedStrEnum handles multiple consecutive underscores correctly."""

    class TestEnum(HyphenatedStrEnum):
        A_B_C = auto()
        MULTI__UNDERSCORE = auto()

    assert_that(TestEnum.A_B_C.value).is_equal_to("a-b-c")
    assert_that(TestEnum.MULTI__UNDERSCORE.value).is_equal_to("multi--underscore")


def test_git_ref_enum_uses_upper_case() -> None:
    """GitRef enum correctly uses UpperCaseStrEnum to produce uppercase values."""
    from lintro.enums.git_ref import GitRef

    assert_that(GitRef.HEAD.value).is_equal_to("HEAD")


def test_git_command_enum_uses_hyphenated() -> None:
    """GitCommand enum correctly uses HyphenatedStrEnum to produce hyphenated values."""
    from lintro.enums.git_command import GitCommand

    assert_that(GitCommand.DESCRIBE.value).is_equal_to("describe")
    assert_that(GitCommand.REV_PARSE.value).is_equal_to("rev-parse")
    assert_that(GitCommand.LOG.value).is_equal_to("log")
