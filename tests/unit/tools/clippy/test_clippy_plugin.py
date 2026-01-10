"""Unit tests for clippy plugin."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.tools.definitions.clippy import (
    CLIPPY_DEFAULT_PRIORITY,
    CLIPPY_DEFAULT_TIMEOUT,
    CLIPPY_FILE_PATTERNS,
    _build_clippy_command,
    _find_cargo_root,
)

if TYPE_CHECKING:
    from lintro.tools.definitions.clippy import ClippyPlugin


# Tests for _find_cargo_root helper


def test_find_cargo_root_finds_cargo_toml_in_current_dir(tmp_path: Path) -> None:
    """Find Cargo.toml in current directory.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text('[package]\nname = "test"')

    rust_file = tmp_path / "src" / "main.rs"
    rust_file.parent.mkdir(parents=True)
    rust_file.write_text("fn main() {}")

    result = _find_cargo_root([str(rust_file)])

    assert_that(result).is_not_none()
    assert_that(str(result)).is_equal_to(str(tmp_path))


def test_find_cargo_root_finds_cargo_toml_in_parent(tmp_path: Path) -> None:
    """Find Cargo.toml in parent directory.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text('[package]\nname = "test"')

    rust_file = tmp_path / "src" / "lib" / "mod.rs"
    rust_file.parent.mkdir(parents=True)
    rust_file.write_text("pub fn hello() {}")

    result = _find_cargo_root([str(rust_file)])

    assert_that(result).is_not_none()
    assert_that(str(result)).is_equal_to(str(tmp_path))


def test_find_cargo_root_returns_none_when_no_cargo_toml(tmp_path: Path) -> None:
    """Return None when no Cargo.toml found.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    rust_file = tmp_path / "main.rs"
    rust_file.write_text("fn main() {}")

    result = _find_cargo_root([str(rust_file)])

    assert_that(result).is_none()


def test_find_cargo_root_handles_directory_input(tmp_path: Path) -> None:
    """Handle directory path input.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text('[package]\nname = "test"')

    result = _find_cargo_root([str(tmp_path)])

    assert_that(result).is_not_none()
    assert_that(str(result)).is_equal_to(str(tmp_path))


def test_find_cargo_root_handles_multiple_paths_same_root(tmp_path: Path) -> None:
    """Handle multiple paths with same Cargo root.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text('[package]\nname = "test"')

    file1 = tmp_path / "src" / "main.rs"
    file2 = tmp_path / "src" / "lib.rs"
    file1.parent.mkdir(parents=True)
    file1.write_text("fn main() {}")
    file2.write_text("pub fn lib() {}")

    result = _find_cargo_root([str(file1), str(file2)])

    assert_that(result).is_not_none()
    assert_that(str(result)).is_equal_to(str(tmp_path))


# Tests for _build_clippy_command helper


def test_build_clippy_command_check_command() -> None:
    """Build check command without fix flag."""
    result = _build_clippy_command(fix=False)

    assert_that(result).contains("cargo", "clippy")
    assert_that("--fix" in result).is_false()
    assert_that("--message-format=json" in result).is_true()


def test_build_clippy_command_fix_command() -> None:
    """Build fix command with fix flag."""
    result = _build_clippy_command(fix=True)

    assert_that(result).contains("cargo", "clippy", "--fix")
    assert_that("--allow-dirty" in result).is_true()
    assert_that("--allow-staged" in result).is_true()


# Tests for ClippyPlugin.definition property


@pytest.mark.parametrize(
    ("attr", "expected"),
    [
        ("name", "clippy"),
        ("can_fix", True),
        ("file_patterns", CLIPPY_FILE_PATTERNS),
        ("priority", CLIPPY_DEFAULT_PRIORITY),
        ("default_timeout", CLIPPY_DEFAULT_TIMEOUT),
    ],
)
def test_clippy_plugin_definition(
    clippy_plugin: ClippyPlugin,
    attr: str,
    expected: object,
) -> None:
    """Definition has correct attributes.

    Args:
        clippy_plugin: The ClippyPlugin instance to test.
        attr: The attribute name to check.
        expected: The expected value for the attribute.
    """
    assert_that(getattr(clippy_plugin.definition, attr)).is_equal_to(expected)


# Tests for ClippyPlugin.set_options method


def test_clippy_plugin_set_timeout(clippy_plugin: ClippyPlugin) -> None:
    """Set timeout option.

    Args:
        clippy_plugin: The ClippyPlugin instance to test.
    """
    clippy_plugin.set_options(timeout=180)
    assert_that(clippy_plugin.options.get("timeout")).is_equal_to(180)


def test_clippy_plugin_set_no_options(clippy_plugin: ClippyPlugin) -> None:
    """Handle no options set.

    Args:
        clippy_plugin: The ClippyPlugin instance to test.
    """
    clippy_plugin.set_options()
    # Should not raise


# Tests for clippy module constants


@pytest.mark.parametrize(
    ("constant", "expected"),
    [
        (CLIPPY_DEFAULT_TIMEOUT, 120),
        (CLIPPY_DEFAULT_PRIORITY, 85),
    ],
)
def test_clippy_constants(constant: int, expected: int) -> None:
    """Verify clippy constants have correct values.

    Args:
        constant: The constant value to check.
        expected: The expected value for the constant.
    """
    assert_that(constant).is_equal_to(expected)


def test_clippy_file_patterns() -> None:
    """Verify file patterns constant."""
    assert_that(CLIPPY_FILE_PATTERNS).contains("*.rs", "Cargo.toml")
