"""Unit tests for rustfmt plugin."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.enums.tool_type import ToolType
from lintro.tools.definitions.rustfmt import (
    RUSTFMT_DEFAULT_TIMEOUT,
    RustfmtPlugin,
)


@pytest.fixture
def rustfmt_plugin() -> RustfmtPlugin:
    """Provide a RustfmtPlugin instance for testing.

    Returns:
        A RustfmtPlugin instance.
    """
    return RustfmtPlugin()


def test_definition_name(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the tool name.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    assert_that(rustfmt_plugin.definition.name).is_equal_to("rustfmt")


def test_definition_can_fix(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the tool can fix issues.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    assert_that(rustfmt_plugin.definition.can_fix).is_true()


def test_definition_tool_type(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the tool type is FORMATTER.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    assert_that(rustfmt_plugin.definition.tool_type).is_equal_to(ToolType.FORMATTER)


def test_definition_file_patterns(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the file patterns.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    patterns = rustfmt_plugin.definition.file_patterns
    assert_that(patterns).contains("*.rs")


def test_definition_priority(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the priority is 80.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    assert_that(rustfmt_plugin.definition.priority).is_equal_to(80)


def test_definition_timeout(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the default timeout.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    assert_that(rustfmt_plugin.definition.default_timeout).is_equal_to(
        RUSTFMT_DEFAULT_TIMEOUT,
    )


def test_definition_native_configs(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify the native config files.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    configs = rustfmt_plugin.definition.native_configs
    assert_that(configs).contains("rustfmt.toml")
    assert_that(configs).contains(".rustfmt.toml")


def test_set_options_timeout(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify timeout option can be set.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    rustfmt_plugin.set_options(timeout=120)
    assert_that(rustfmt_plugin.options.get("timeout")).is_equal_to(120)


def test_set_options_invalid_timeout(rustfmt_plugin: RustfmtPlugin) -> None:
    """Verify invalid timeout raises ValueError.

    Args:
        rustfmt_plugin: The plugin instance.
    """
    with pytest.raises(ValueError):
        rustfmt_plugin.set_options(timeout=-1)


def test_check_no_cargo_toml(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check skips gracefully when no Cargo.toml found.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    test_file = tmp_path / "test.rs"
    test_file.write_text("fn main() {}")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        result = rustfmt_plugin.check([str(test_file)], {})

    # When no Cargo.toml found, the tool skips gracefully with success
    assert_that(result.output).contains("No Cargo.toml found")


def test_check_success(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check returns success when no formatting issues found.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    # Create a Cargo.toml to satisfy the check
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"')

    test_file = tmp_path / "src" / "main.rs"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("fn main() {}\n")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            rustfmt_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = rustfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)


def test_check_with_issues(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check returns issues when formatting problems found.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"')

    test_file = tmp_path / "src" / "main.rs"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("fn main(){let x=1;}")

    mock_output = "Diff in src/main.rs at line 1:\n-fn main(){let x=1;}\n+fn main() {\n+    let x = 1;\n+}"

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            rustfmt_plugin,
            "_run_subprocess",
            return_value=(False, mock_output),
        ):
            result = rustfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_greater_than(0)


def test_check_timeout(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Check handles timeout correctly.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"')

    test_file = tmp_path / "src" / "main.rs"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("fn main() {}")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            rustfmt_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["cargo", "fmt"], timeout=60),
        ):
            result = rustfmt_plugin.check([str(test_file)], {})

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")


def test_fix_success(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Fix applies formatting successfully.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"')

    test_file = tmp_path / "src" / "main.rs"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("fn main(){}")

    call_count = 0

    def mock_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First check - issues found
            return (False, "Diff in src/main.rs at line 1:")
        elif call_count == 2:
            # Fix command
            return (True, "")
        else:
            # Verification - no issues
            return (True, "")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(rustfmt_plugin, "_run_subprocess", side_effect=mock_run):
            result = rustfmt_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.fixed_issues_count).is_equal_to(1)


def test_fix_no_issues(
    rustfmt_plugin: RustfmtPlugin,
    tmp_path: Path,
) -> None:
    """Fix returns early when no issues to fix.

    Args:
        rustfmt_plugin: The plugin instance.
        tmp_path: Temporary directory path.
    """
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text('[package]\nname = "test"\nversion = "0.1.0"')

    test_file = tmp_path / "src" / "main.rs"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("fn main() {}\n")

    with patch(
        "lintro.plugins.execution_preparation.verify_tool_version",
        return_value=None,
    ):
        with patch.object(
            rustfmt_plugin,
            "_run_subprocess",
            return_value=(True, ""),
        ):
            result = rustfmt_plugin.fix([str(test_file)], {})

    assert_that(result.success).is_true()
    assert_that(result.issues_count).is_equal_to(0)
    assert_that(result.fixed_issues_count).is_equal_to(0)
